"""Generate a complete native strategy and paired Pine delivery. MPL-2.0."""
import hashlib,json
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from update_pine_script import EVENT_PATTERN
from pine_initialization import check_initialization,END
ROOT=Path(__file__).resolve().parent.parent
TAIPEI=ZoneInfo('Asia/Taipei')

def previous_session(day,calendar):
    # Saved annual calendar only; never fetch a calendar while generating Pine.
    for _ in range(370):
        entry=calendar.get('days',{}).get(day.isoformat())
        closed=calendar.get('closure_overrides',{}).get(day.isoformat())
        if day.weekday()<5 and not closed and (entry is None or entry.get('open') is True):return day
        day-=timedelta(days=1)
    raise ValueError('no_default_session_in_saved_calendar')

def coverage():
    control=json.loads((ROOT/'data/history_completion_control.json').read_text())
    cutoffs=[datetime.fromisoformat(control['cutoff_utc'])]
    live=ROOT/'data/live_control.json'
    if live.exists():
        sources=json.loads(live.read_text()).get('sources',{})
        ends=[s.get('completed_until') for s in sources.values()]
        if len(ends)==2 and all(ends):cutoffs.append(min(datetime.fromisoformat(x) for x in ends))
    cutoff=max(cutoffs).astimezone(TAIPEI)
    calendar_path=ROOT/'data/trading_calendar.json'
    calendar=json.loads(calendar_path.read_text()) if calendar_path.exists() else {}
    return cutoff,previous_session(cutoff.date(),calendar)

def build():
    source=(ROOT/'candidates/8zz-history-latest.pine').read_text()
    start=source.index('var int[] evt_time');end=source.index(END)+len(END)
    before=EVENT_PATTERN.findall(source)
    cutoff,default_end=coverage()
    header=(ROOT/'scripts/pine_templates/strategy_header.pine').read_text()
    header=header.replace('__DEFAULT_END_TIMESTAMP__',default_end.strftime('%d %b %Y')+' 00:00 +0800').replace('__DATA_CUTOFF_TAIPEI__',cutoff.isoformat())
    engine=(ROOT/'scripts/pine_templates/strategy_engine.pine').read_text()
    result=header+source[start:end]+'\n\n'+engine+'\n'
    after=EVENT_PATTERN.findall(result)
    if before!=after or not after:raise ValueError('strategy_changed_saved_events')
    checks=check_initialization(result)
    source_sha=hashlib.sha256(source.encode()).hexdigest();strategy_sha=hashlib.sha256(result.encode()).hexdigest()
    checks.update(same_bar_policy='latest_post_before_filters',events=len(after),events_unchanged=True,source_sha256=source_sha,strategy_sha256=strategy_sha,
        data_cutoff_taipei=cutoff.isoformat(),default_end_date=default_end.isoformat(),event_scope='all_saved_indicator_events',
        tradingview_compiled=False,order_api='TradingView strategy broker emulator only')
    out=ROOT/'candidates/8zz-strategy-latest.pine';out.write_text(result)
    out.with_suffix('.checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    delivery={'schema':1,'events':len(after),'same_event_tuples':True,'same_bar_policy':'latest_post_before_filters','data_cutoff_taipei':cutoff.isoformat(),
        'event_fields_sha256':hashlib.sha256(json.dumps(after,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
        'event_encoding':checks.get('event_encoding'),'packed_event_round_trip':checks.get('packed_event_round_trip'),
        'strategy_default_end_date':default_end.isoformat(),'tradingview_compiled':False,
        'indicator':{'path':'candidates/8zz-history-latest.pine','sha256':source_sha},
        'strategy':{'path':'candidates/8zz-strategy-latest.pine','sha256':strategy_sha}}
    (ROOT/'candidates/8zz-pine-delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(checks,ensure_ascii=False));return result
if __name__=='__main__':build()
