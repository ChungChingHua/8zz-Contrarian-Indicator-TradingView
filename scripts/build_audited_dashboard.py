"""Read saved judgments only. No AI, acquisition, schedules or deployment. MPL-2.0.
All account trades use 0050 proxy; typed market bars prevent interval substitution.
"""
import argparse, hashlib, json, re, urllib.request
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from update_pine_script import EVENT_PATTERN
ROOT=Path(__file__).resolve().parent.parent
UTC=timezone.utc

def read(path): return json.loads((ROOT/path).read_text())
def iso(ms): return datetime.fromtimestamp(ms/1000,UTC).isoformat()
def fetch_market():
    previous=read('data/dashboard_market.json') if (ROOT/'data/dashboard_market.json').exists() else {}
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
            if not bars:raise ValueError('empty_market_response')
            payload['series'][interval]=sorted(bars,key=lambda x:x['time'])
            payload.setdefault('sources',{})[interval]=url
        except Exception as e:payload['errors'].append({'interval':interval,'error':type(e).__name__})
    for interval in ('1d','30m'):
        if not payload['series'].get(interval):
            payload['series'][interval]=previous.get('series',{}).get(interval,[])
    if payload['errors']:
        payload['last_attempt_at']=payload['fetched_at']
        payload['fetched_at']=previous.get('fetched_at')
    (ROOT/'data/dashboard_market.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    return payload

def events():
    old=read('docs/events.json')['events']
    sources={e['unix_ms']:e.get('source_url','') for e in old}
    posts=read('data/social_posts.json')
    for p in posts.values():sources[p['unix_ms']]=p['url']
    from history_completion import ledger_records, archive
    records,_=ledger_records()
    all_posts=archive()
    by_time={r['unix_ms']:r for r in records.values() if r['status']=='completed_signal'}
    baseline_path=ROOT/'data/event_baseline_keys.json'
    baseline=set(json.loads(baseline_path.read_text())) if baseline_path.exists() else set()
    out=[];direction=0
    for i,m in enumerate(EVENT_PATTERN.finditer((ROOT/'candidates/8zz-history-latest.pine').read_text())):
        ts,d,s,tip,ticker=m.groups();ts=int(ts);d=int(d)
        tip=tip.replace('\\n','\n').replace('\\"','"')
        urls=re.findall(r'https://[^\s\\]+',tip)
        urls=list(dict.fromkeys(([sources[ts]] if sources.get(ts) else [])+urls))
        platform=' / '.join(x for x,domain in [('Facebook','facebook.com'),('Threads','threads.')] if any(domain in u for u in urls)) or ('Threads' if 'Threads' in tip else 'Facebook（歷史註記）')
        flip=d!=0 and d!=direction
        if d:direction=d
        r=by_time.get(ts,{})
        completed=r.get('completed_at') # No old dispatch time, ledger mtime or present time substitutions.
        key=hashlib.sha256(json.dumps([ts,d,int(s),tip,ticker],ensure_ascii=False).encode()).hexdigest()
        fetched=next((all_posts[m['key']].get('fetched_at') for m in r.get('members',[]) if m['key'] in all_posts and all_posts[m['key']].get('fetched_at')),None)
        live_posts=read('data/live_posts.json') if (ROOT/'data/live_posts.json').exists() else {}
        historical=not r.get('key') or r['key'] not in live_posts
        if completed and datetime.fromisoformat(completed).astimezone(ZoneInfo('Asia/Taipei')).date()>datetime.fromtimestamp(ts/1000,ZoneInfo('Asia/Taipei')).date():historical=True
        extra={'event_key':key,'completed_at':completed,'fetched_at':fetched,
            'available_ms':int(datetime.fromisoformat(completed).timestamp()*1000) if completed else None,
            'sentiment':r.get('processed',{}).get('reasoning','原歷史只保存反指標方向，未另存原文情緒欄位'),
            'historical':historical,
            'baseline':key in baseline,'media_note':json.dumps(r.get('media_scope',{}),ensure_ascii=False) if r else '原歷史無媒體分析範圍紀錄'}
        out.append({**extra,'id':i+1,'unix_ms':ts,'time':iso(ts),'direction':d,'strength':int(s),'summary':tip,'target':ticker or '未辨識','symbol':'0050.TW','proxy':True,'urls':urls,'platform':platform,'is_flip':flip})
    return out

def next_bar(bars,ts):return next((b for b in bars if b['time']>ts),None)
def outcome(direction,entry,exit):return direction*(exit/entry-1)*100

def simulate(ev,bars,mode,hold=17,basis='published'):
    if basis=='available':
        unknown=[e for e in ev if e.get('available_ms') is None]
        known=sorted((dict(e,unix_ms=max(e['available_ms'],e['unix_ms'])) for e in ev if e.get('available_ms') is not None),key=lambda e:(e['unix_ms'],e['id']))
        direction=0
        for e in known:
            e['is_flip']=bool(e['direction'] and e['direction']!=direction)
            if e['direction']:direction=e['direction']
        result=simulate(known,bars,mode,hold)
        for e in unknown:result['rows'][str(e['id'])]={'status':'缺歷史判讀完成時間，不計可成交績效','trade':False,'missing':True}
        result['stats']['missing']+=len(unknown)
        result['stats']['missing_completion']=len(unknown)
        return result
    ev=sorted(ev,key=lambda e:(e['unix_ms'],e['id']))
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
        if mode=='A' and any(b.get('gap_before') for b in bars[pos+1:pos+hold+1]):
            base.update(status='固定持有期間存在缺漏30分鐘行情',missing=True);continue
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
    build(args.refresh_market)

def build(refresh_market=False):
    market=fetch_market() if refresh_market else read('data/dashboard_market.json')
    imported=read('data/shioaji_market_import.json') if (ROOT/'data/shioaji_market_import.json').exists() else {}
    stock=imported.get('symbols',{}).get('0050',{})
    if imported.get('status')=='completed' and all(stock.get('series',{}).get(i) for i in ('30m','1d')):
        old_daily={b['time']:b for b in market['series'].get('1d',[])}
        if any(abs(b['price']/old_daily[b['time']]['price']-1)>0.00001 for b in stock['series']['1d'] if b['time'] in old_daily):raise ValueError('daily_quote_source_conflict')
        old_daily.update({b['time']:b for b in stock['series']['1d']})
        market={'symbol':'0050.TW','series':{'30m':stock['series']['30m'],'1d':sorted(old_daily.values(),key=lambda b:b['time'])},'fetched_at':imported['fetched_at'],'errors':[],'source':'Sinopac Shioaji'}
    ev=events();summary=read('data/history_completion_summary.json')
    (ROOT/'data/signal_events.json').write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n')
    inventory=read('data/history_completion_inventory.json')
    from publication_scope import scope
    ev,inventory,market,summary,publication=scope(ev,inventory,market,read('data/publication_policy.json'))
    pine=(ROOT/'candidates/8zz-history-latest.pine').read_text();hold=int(re.search(r'holdBars = input.int\((\d+)',pine)[1])
    sources=read('data/history_completion_control.json').get('sources',{})
    live=read('data/live_control.json') if (ROOT/'data/live_control.json').exists() else {}
    result={'publication':publication,'events':ev,'history':{k:summary[k] for k in ('post_status_counts','archive_posts','remaining_not_started_groups','latest_signal_date')},'inventory':[{k:r.get(k) for k in ('url','display_time','status')} for r in inventory],'market':{k:market[k] for k in ('symbol','fetched_at','series','errors')},'hold_bars':hold,'built_at':datetime.now(UTC).isoformat(),
        'platform_cutoffs':{k:min(v.get('completed_until') or publication['before'],publication['before']) for k,v in (live.get('sources') or sources).items()},
        'live_status':{'enabled':read('data/live_settings.json').get('enabled',False) if (ROOT/'data/live_settings.json').exists() else False,'ai_stop':bool(live.get('ai_stop')),'notifications':'通知狀態由後端管理'},
        'modes':{m:simulate(ev,market['series'].get('30m' if m=='A' else '1d',[]),m,hold) for m in ['A','B']},
        'available_modes':{m:simulate(ev,market['series'].get('30m' if m=='A' else '1d',[]),m,hold,'available') for m in ['A','B']}}
    from futures_performance import simulate_futures,daytime_only
    imported=read('data/shioaji_market_import.json') if (ROOT/'data/shioaji_market_import.json').exists() else {}
    futures=imported.get('symbols',{}).get('TXF',{})
    cutoff=int(datetime.fromisoformat(publication['before']).timestamp()*1000)
    fs={k:[b for b in futures.get('series',{}).get(k,[]) if b['time']<cutoff] for k in ('30m','1d')}
    fs=daytime_only(fs)
    fm={'symbol':'TXFR1','fetched_at':imported.get('fetched_at'),'series':fs,'errors':futures.get('errors',[])}
    result['instruments']={'TXF':{'name':'台指期貨・日盤 TXFR1','market':fm,
       'modes':{m:simulate_futures(ev,fs['30m' if m=='A' else '1d'],m,hold) for m in ('A','B')},
       'available_modes':{m:simulate_futures(ev,fs['30m' if m=='A' else '1d'],m,hold,'available') for m in ('A','B')},
       'disclosure':'TXFR1 未調整近月連續資料；結算週及跨換約區段交易排除，不銜接價差獲利。結算週採每月第三個星期三所在週的保守範圍，非已驗證逐月轉倉。僅使用08:45–13:45日盤行情，A持有17根日盤30分鐘棒，B採完整日盤收盤；夜間訊號順延下個有效日盤成交時點。非強制當沖，跨日持倉價差仍反映於次日日盤價格。等額名目本金1倍報酬，不是保證金報酬；未含每點200元口數、費稅、滑價與追繳。'}}
    from public_dashboard import finalize
    result=finalize(result, ROOT/'docs')
    from publication_scope import assert_boundary
    assert_boundary(result)
    text=json.dumps(result,ensure_ascii=False,separators=(',',':'))
    (ROOT/'docs/dashboard-data.json').write_text(text+'\n')
    (ROOT/'docs/dashboard-data.js').write_text('window.DASHBOARD_DATA='+text.replace('</','<\\/')+';\n')
    manifest={'schema':1,'version':result['version'],'url':'snapshots/'+result['version']+'.json'}
    snapshot=ROOT/'docs'/manifest['url'];snapshot.parent.mkdir(exist_ok=True)
    snapshot.write_text(text+'\n')
    (ROOT/'docs/data-version.json').write_text(json.dumps(manifest)+'\n')
    # Self-contained preview opens directly with file://; no server or CDN needed.
    html=(ROOT/'docs/index.html').read_text()
    html=html.replace('<link rel="stylesheet" href="dashboard.css">','<style>'+(ROOT/'docs/dashboard.css').read_text()+'</style>')
    html=html.replace('<script src="dashboard-data.js" defer></script>','').replace('<script src="dashboard.js" defer></script>','')
    html=html.replace('</body>','<script>window.INLINE_PREVIEW=true;window.DASHBOARD_DATA='+text.replace('</','<\\/')+';</script><script>'+(ROOT/'docs/dashboard.js').read_text()+'</script></body>')
    (ROOT/'docs/preview.html').write_text(html)
    print(json.dumps({m:r['stats'] for m,r in result['modes'].items()},ensure_ascii=False))
    return result
def publish_saved_dashboard(remote):
    """Project acknowledged judgments; shared by live and historical report paths."""
    import history_completion as hc
    build(refresh_market=False)
    remote.save('data/signal_events.json',read('data/signal_events.json'))
    version=read('docs/data-version.json')['version']
    # The version pointer is always acknowledged last.
    for path in ('docs/dashboard-data.json','docs/dashboard-data.js','docs/preview.html',
                 'docs/snapshots/'+version+'.json','docs/data-version.json'):
        hc.publish_text(remote,path,(ROOT/path).read_text())

if __name__=='__main__':main()
