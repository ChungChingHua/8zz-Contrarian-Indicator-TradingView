"""Read-only historical quotes. No account output, subscriptions, CA or orders. MPL-2.0."""
import os,json,math,sys,time,calendar
from pathlib import Path
from datetime import datetime,date,timedelta,timezone
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Asia/Taipei');ROOT=Path(__file__).resolve().parent.parent
OUTPUT=ROOT/'data/shioaji_market_import.json'

def aggregate(raw,symbol):
    buckets={};days={};valid=0
    for ns,price in zip(raw['ts'],raw['Close']):
        price=float(price)
        if not math.isfinite(price) or price<=0:continue
        # SDK ns values encode Taiwan wall-clock, as in official DataFrame examples.
        t=datetime.fromtimestamp(int(ns)/1e9,timezone.utc).replace(tzinfo=TZ)
        minute=t.hour*60+t.minute
        if t.second or t.microsecond:raise ValueError('unexpected_bar_timestamp')
        if symbol=='0050':start,end=540,810
        elif 525<minute<=825:start,end=525,825
        elif minute>900:start,end=900,1440
        elif minute<=300:start,end=0,300
        else:continue
        if not start<minute<=end:continue
        anchor=t.replace(hour=0,minute=0,second=0,microsecond=0)
        close=start+((minute-start+29)//30)*30
        close_t=anchor+timedelta(minutes=close)
        bucket=buckets.setdefault(int(close_t.timestamp()*1000),{})
        if minute in bucket and bucket[minute]!=price:raise ValueError('conflicting_minute')
        bucket[minute]=price;valid+=1
        if (symbol=='0050' or 525<minute<=825):days.setdefault(t.date(),{})[minute]=price
    bars=[{'time':ts,'price':v[max(v)]} for ts,v in sorted(buckets.items()) if len(v)==30 or (symbol=='0050' and len(v)==26 and max(v)==810 and set(range(806,810)).isdisjoint(v))]
    missing=sorted(ts for ts in buckets if ts not in {b['time'] for b in bars})
    previous=None
    for bar in bars:
        if previous is not None and any(previous<t<=bar['time'] for t in missing):bar['gap_before']=True
        previous=bar['time']
    daily=[]
    expected=266 if symbol=='0050' else 300;ending=810 if symbol=='0050' else 825
    for day,v in sorted(days.items()):
        if len(v)==expected and ending in v:
            dt=datetime.combine(day,datetime.min.time(),TZ)+timedelta(minutes=ending)
            daily.append({'time':int(dt.timestamp()*1000),'price':v[ending]})
    return {'30m':bars,'1d':daily},{'valid_minutes':valid,'incomplete_30m_buckets':len(buckets)-len(bars),'missing_bucket_times':[ts for ts in buckets if ts not in {b['time'] for b in bars}],'complete_30m_bars':len(bars),'complete_daily_bars':len(daily)}

def months(start,end):
    while start<=end:
        last=min(date(start.year,start.month,calendar.monthrange(start.year,start.month)[1]),end)
        yield start,last
        start=last+timedelta(days=1)

def run():
    result={'source':'Sinopac Shioaji','sdk':'1.7.11','requested_start':'2025-12-01','requested_end':'2026-09-30','fetched_at':datetime.now(timezone.utc).isoformat(),'symbols':{},'status':'running','error':None}
    def save():OUTPUT.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    save()
    key=os.environ.pop('SHIOAJI_API_KEY','');secret=os.environ.pop('SHIOAJI_SECRET_KEY','')
    if not key or not secret:
        result.update(status='failed',error='missing_shioaji_repository_secrets');save();return 1
    api=None
    try:
        # Suppress native SDK/account callbacks at fd level, not just Python print.
        with open(os.devnull,'w') as sink:
            out,err=os.dup(1),os.dup(2);os.dup2(sink.fileno(),1);os.dup2(sink.fileno(),2)
            try:
                import shioaji as sj
                api=sj.Shioaji(simulation=False)
                api.login(api_key=key,secret_key=secret)
                key=secret=''
                for symbol,code in [('0050','0050'),('TXF','TXFR1')]:
                    contract=api.contracts.get(code)
                    if contract is None:raise ValueError('quote_contract_not_available')
                    data={'code':code,'series':{'30m':[],'1d':[]},'chunks':[],'errors':[]}
                    result['symbols'][symbol]=data
                    chunks=[(date(2026,9,1),date(2026,9,1))] if os.getenv('QUOTE_INSPECT')=='1' else months(date(2025,12,1),date(2026,9,30))
                    for a,b in chunks:
                        raw=api.kbars(contract=contract,start=a.isoformat(),end=b.isoformat())
                        raw=raw.dict() if hasattr(raw,'dict') else dict(raw)
                        series,counts=aggregate(raw,symbol)
                        counts['timestamp_samples']=[datetime.fromtimestamp(int(ns)/1e9,timezone.utc).isoformat() for ns in list(raw['ts'][:3])+list(raw['ts'][-3:])]
                        counts['raw_count']=len(raw['ts'])
                        if not series['30m']:raise ValueError('no_complete_30m_bars_in_month')
                        for interval,rows in series.items():data['series'][interval].extend(rows)
                        data['chunks'].append({'start':a.isoformat(),'end':b.isoformat(),**counts});save();time.sleep(1)
                result['status']='completed'
            finally:
                if api:
                    try:api.logout()
                    except Exception:pass
                sys.stdout.flush();sys.stderr.flush()
                import ctypes
                ctypes.CDLL(None).fflush(None)
                os.dup2(out,1);os.dup2(err,2);os.close(out);os.close(err)
    except Exception as e:result.update(status='failed',error=type(e).__name__) # Never stringify provider/account errors.
    save();print(json.dumps({'status':result['status'],'error':result['error'],'symbols':list(result['symbols'])}));return 0 if result['status']=='completed' else 1
if __name__=='__main__':sys.exit(run())
