"""Read saved judgments only. No AI, acquisition, schedules or deployment. MPL-2.0.
All account trades use 0050 proxy; typed market bars prevent interval substitution.
"""
import argparse, json, re, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from update_pine_script import EVENT_PATTERN
ROOT=Path(__file__).resolve().parent.parent
UTC=timezone.utc

def read(path): return json.loads((ROOT/path).read_text())
def iso(ms): return datetime.fromtimestamp(ms/1000,UTC).isoformat()
def fetch_market():
    payload={'symbol':'0050.TW','fetched_at':datetime.now(UTC).isoformat(),'series':{},'errors':[]}
    for interval,period in [('1d','2y'),('30m','1mo')]:
        url=f'https://r.jina.ai/http://query1.finance.yahoo.com/v8/finance/chart/0050.TW?range={period}&interval={interval}'
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'8zz-audit/1.0'})
            with urllib.request.urlopen(req,timeout=45) as r: text=r.read().decode()
            data=json.loads(text[text.index('{'):])['chart']['result'][0]
            bars=[]
            for ts,price in zip(data['timestamp'],data['indicators']['quote'][0]['close']):
                # Yahoo timestamps are bar opens; Taiwan regular daily closes at 13:30.
                close=ts+16200 if interval=='1d' else min(ts+1800, int(datetime.fromtimestamp(ts,UTC).replace(hour=5,minute=30,second=0).timestamp()))
                if price is not None and price>0 and close<=datetime.now(UTC).timestamp():
                    bars.append({'time':close*1000,'price':price})
            payload['series'][interval]=sorted(bars,key=lambda x:x['time'])
            payload.setdefault('sources',{})[interval]=url
        except Exception as e:payload['errors'].append({'interval':interval,'error':type(e).__name__})
    (ROOT/'data/dashboard_market.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    return payload

def events():
    old=read('docs/events.json')['events']
    sources={e['unix_ms']:e.get('source_url','') for e in old}
    posts=read('data/social_posts.json')
    for p in posts.values():sources[p['unix_ms']]=p['url']
    out=[];direction=0
    for i,m in enumerate(EVENT_PATTERN.finditer((ROOT/'candidates/8zz-history-latest.pine').read_text())):
        ts,d,s,tip,ticker=m.groups();ts=int(ts);d=int(d)
        tip=tip.replace('\\n','\n').replace('\\"','"')
        urls=re.findall(r'https://[^\s\\]+',tip)
        urls=list(dict.fromkeys(([sources[ts]] if sources.get(ts) else [])+urls))
        platform=' / '.join(x for x,domain in [('Facebook','facebook.com'),('Threads','threads.')] if any(domain in u for u in urls)) or ('Threads' if 'Threads' in tip else 'Facebook（歷史註記）')
        flip=d!=0 and d!=direction
        if d:direction=d
        out.append({'id':i+1,'unix_ms':ts,'time':iso(ts),'direction':d,'strength':int(s),'summary':tip,'target':ticker or '未辨識','symbol':'0050.TW','proxy':True,'urls':urls,'platform':platform,'is_flip':flip})
    return out

def next_bar(bars,ts):return next((b for b in bars if b['time']>ts),None)
def outcome(direction,entry,exit):return direction*(exit/entry-1)*100

def simulate(ev,bars,mode,hold=17):
    rows={str(e['id']):{'status':'中性觀察' if not e['direction'] else '同方向補充，不另進場','trade':False} for e in ev}
    candidates={}
    for e in ev:
        if not e['is_flip']:continue
        ent=next_bar(bars,e['unix_ms'])
        if not ent or ent['time']-e['unix_ms']>7*86400000:
            rows[str(e['id'])].update(status='缺訊號附近行情' if ent else '缺進場行情',missing=True);continue
        # All signals known before a single close produce one final desired direction.
        if ent['time'] in candidates:
            previous=candidates[ent['time']][0]
            rows[str(previous['id'])]['status']='同收盤訊號合併，以最後方向執行'
        candidates[ent['time']]=(e,ent)
    effective=[];desired=0
    for e,ent in candidates.values():
        if e['direction']==desired:
            rows[str(e['id'])]['status']='同收盤淨方向未改變，不另進場';continue
        desired=e['direction'];effective.append((e,ent))
    trades=[];busy_until=0
    for n,(e,ent) in enumerate(effective):
        base=rows[str(e['id'])]
        if ent['time']<=busy_until:
            base['status']='固定持有中，不重疊進場';continue
        pos=bars.index(ent)
        ex=(bars[pos+hold] if pos+hold<len(bars) else None) if mode=='A' else (effective[n+1][1] if n+1<len(effective) else None)
        base.update(trade=True,entry=ent,exit=ex,direction=e['direction'],event_id=e['id'])
        if ex:
            pnl=outcome(e['direction'],ent['price'],ex['price'])
            base.update(status='已結算',pnl=pnl,result='勝' if pnl>1e-9 else '敗' if pnl<-1e-9 else '平手')
            busy_until=ex['time']-(1 if mode=='B' else 0)
        else:
            mark=bars[-1];base.update(status='未平倉',mark=mark,floating=outcome(e['direction'],ent['price'],mark['price']))
            busy_until=float('inf')
        trades.append(base)
    settled=[t for t in trades if t['exit']]
    stats={'settled':len(settled),'wins':sum(t['result']=='勝' for t in settled),'losses':sum(t['result']=='敗' for t in settled),'ties':sum(t['result']=='平手' for t in settled),'open':sum(not t['exit'] for t in trades),'missing':sum(r.get('missing',False) for r in rows.values())}
    stats['win_rate']=stats['wins']/len(settled)*100 if settled else None
    stats['average']=sum(t['pnl'] for t in settled)/len(settled) if settled else None
    curve=[]
    if trades:
        start=trades[0]['entry'];capital=100.;finished=set()
        for b in bars:
            if b['time']<start['time']:continue
            active=None
            for i,t in enumerate(trades):
                if t['exit'] and t['exit']['time']<=b['time'] and i not in finished:
                    capital*=1+t['pnl']/100;finished.add(i)
                if t['entry']['time']<=b['time'] and (not t['exit'] or b['time']<t['exit']['time']):active=t
            equity=capital*(1+outcome(active['direction'],active['entry']['price'],b['price'])/100) if active else capital
            curve.append({'time':b['time'],'equity':equity,'benchmark':100*b['price']/start['price']})
    return {'rows':rows,'stats':stats,'trades':trades,'curve':curve}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh-market',action='store_true');args=parser.parse_args()
    market=fetch_market() if args.refresh_market else read('data/dashboard_market.json')
    ev=events();summary=read('data/history_completion_summary.json')
    pine=(ROOT/'candidates/8zz-history-latest.pine').read_text();hold=int(re.search(r'holdBars = input.int\((\d+)',pine)[1])
    result={'events':ev,'history':summary,'inventory':read('data/history_completion_inventory.json'),'market':market,'hold_bars':hold,'built_at':datetime.now(UTC).isoformat(),'modes':{m:simulate(ev,market['series'].get('30m' if m=='A' else '1d',[]),m,hold) for m in ['A','B']}}
    text=json.dumps(result,ensure_ascii=False,separators=(',',':'))
    (ROOT/'docs/dashboard-data.json').write_text(text+'\n')
    (ROOT/'docs/dashboard-data.js').write_text('window.DASHBOARD_DATA='+text.replace('</','<\\/')+';\n')
    # Self-contained preview opens directly with file://; no server or CDN needed.
    html=(ROOT/'docs/index.html').read_text()
    html=html.replace('<link rel="stylesheet" href="dashboard.css">','<style>'+(ROOT/'docs/dashboard.css').read_text()+'</style>')
    html=html.replace('<script src="dashboard-data.js" defer></script>','').replace('<script src="dashboard.js" defer></script>','')
    html=html.replace('</body>','<script>window.DASHBOARD_DATA='+text.replace('</','<\\/')+';</script><script>'+(ROOT/'docs/dashboard.js').read_text()+'</script></body>')
    (ROOT/'docs/preview.html').write_text(html)
    print(json.dumps({m:r['stats'] for m,r in result['modes'].items()},ensure_ascii=False))
if __name__=='__main__':main()
