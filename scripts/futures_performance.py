"""Conservative TXFR1 proxy: exclude settlement-week/cross-regime trades. MPL-2.0."""
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
import copy
TZ=ZoneInfo('Asia/Taipei')
def segment(ts):
    d=datetime.fromtimestamp(ts/1000,TZ).date();first=d.replace(day=1)
    wed=first+timedelta(days=(2-first.weekday())%7+14)
    mon=wed-timedelta(days=2);sat=wed+timedelta(days=3)
    if mon<=d<sat:return None
    return (d.year,d.month,d<mon)
def simulate_futures(events,bars,mode,hold=17,basis='published'):
    from build_audited_dashboard import simulate,outcome
    r=simulate(events,bars,mode,hold,basis);kept=[]
    for t in r['trades']:
        end=t['exit'] or t.get('mark');a=segment(t['entry']['time']);b=segment(end['time'])
        if a is None or b!=a:
            r['rows'][str(t['event_id'])]={'trade':False,'missing':True,'status':'跨結算週／換約未核對，排除績效'}
        else:kept.append(t)
    r['trades']=kept;closed=[t for t in kept if t['exit']];s=r['stats']
    s.update(settled=len(closed),open=len(kept)-len(closed),wins=sum(t['result']=='勝' for t in closed),losses=sum(t['result']=='敗' for t in closed),ties=sum(t['result']=='平手' for t in closed),missing=sum(v.get('missing',False) for v in r['rows'].values()))
    s['win_rate']=s['wins']/len(closed)*100 if closed else None;s['average']=sum(t['pnl'] for t in closed)/len(closed) if closed else None
    curve=[];capital=100.;finished=set()
    if kept:
        start=kept[0]['entry']['time']
        for bar in bars:
            if bar['time']<start:continue
            active=None
            for i,t in enumerate(kept):
                if t['exit'] and t['exit']['time']<=bar['time'] and i not in finished:capital*=1+t['pnl']/100;finished.add(i)
                if t['entry']['time']<=bar['time'] and (not t['exit'] or bar['time']<t['exit']['time']):active=t
            eq=capital*(1+outcome(active['direction'],active['entry']['price'],bar['price'])/100) if active else capital
            curve.append({'time':bar['time'],'equity':eq,'benchmark':100})
    r['curve']=curve
    return r
