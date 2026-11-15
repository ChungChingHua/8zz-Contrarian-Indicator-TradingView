"""Fail-closed TWSE official annual trading calendar. MPL-2.0."""
import argparse
import hashlib
import json
import urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
TAIPEI=ZoneInfo('Asia/Taipei')
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'data/trading_calendar.json'
OPEN_NAMES={'國曆新年開始交易日','農曆春節前最後交易日','農曆春節後開始交易日'}

def parse_official(raw,year,now):
    if raw.get('stat')!='ok' or raw.get('fields')!=['日期','名稱','說明'] or raw.get('queryYear')!=year:
        raise ValueError('official_calendar_schema_or_year_mismatch')
    rows=raw.get('data',[])
    if len(rows)<10:raise ValueError('official_calendar_incomplete')
    special={}
    for d,name,note in rows:
        parsed=date.fromisoformat(d)
        if parsed.year!=year or d in special:raise ValueError('official_calendar_date_mismatch')
        if name in OPEN_NAMES:opened=True
        elif ('放假' in note or '補假' in note) or '無交易' in name:opened=False
        else:raise ValueError('official_calendar_unknown_entry')
        special[d]={'open':opened,'name':name}
    days={};d=date(year,1,1)
    while d.year==year:
        days[d.isoformat()]=special.get(d.isoformat(),{'open':d.weekday()<5,'name':'一般交易日' if d.weekday()<5 else '週末'})
        d+=timedelta(days=1)
    return {'source':'https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=json&queryYear='+str(year-1911),
        'authority':'臺灣證券交易所','year':year,'fetched_at':now.isoformat(),
        'expires_at':(now+timedelta(hours=24)).isoformat(),'raw_sha256':hashlib.sha256(json.dumps(raw,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
        'days':days,'limitation':'年度表未必包含臨時颱風等休市；啟用前及臨時休市時須核對 TWSE 公告並設定停用／closure_overrides。',
        'closure_overrides':{}}

def refresh(now=None):
    now=now or datetime.now(timezone.utc);year=now.astimezone(TAIPEI).year
    url='https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=json&queryYear='+str(year-1911)
    with urllib.request.urlopen(url,timeout=25) as r:raw=json.loads(r.read(1_000_000))
    data=parse_official(raw,year,now)
    if PATH.exists():data['closure_overrides']=json.loads(PATH.read_text()).get('closure_overrides',{})
    PATH.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');return data

def trading_day(calendar,now):
    local=now.astimezone(TAIPEI);day=local.date().isoformat()
    if calendar.get('authority')!='臺灣證券交易所' or calendar.get('year')!=local.year or day not in calendar.get('days',{}):
        raise ValueError('official_trading_calendar_missing_or_wrong_year')
    fetched=datetime.fromisoformat(calendar['fetched_at']);expiry=datetime.fromisoformat(calendar['expires_at'])
    if now<fetched or now>=expiry or expiry-fetched>timedelta(hours=24):raise ValueError('official_trading_calendar_expired')
    return not calendar.get('closure_overrides',{}).get(day) and calendar['days'][day]['open']

def due_slot(now,calendar):
    if not trading_day(calendar,now):return None
    local=now.astimezone(TAIPEI);minute=local.hour*60+local.minute
    if minute<525 or minute>810:return None
    # A delayed Actions invocation belongs only to the current 15-minute interval.
    # No artificial catch-up runs. Next success still covers all un-fetched time.
    slot=(minute-525)//15
    return local.date().isoformat()+'/'+str(slot).zfill(2)

if __name__=='__main__':
    argparse.ArgumentParser().parse_args()
    try:refresh();print('已更新 TWSE 官方開休市表；有效 24 小時，臨時休市公告須另核對')
    except Exception:raise SystemExit('官方交易日資料取得失敗；未替換既有資料，不得開始付費抓取')
