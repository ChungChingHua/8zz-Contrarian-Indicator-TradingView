"""Clearly labeled synthetic preview, never enters production event/ledger files. MPL-2.0."""
import copy,json
from pathlib import Path
from datetime import datetime,timezone
from build_audited_dashboard import simulate,ROOT

def sample():
    data=json.loads((ROOT/'docs/dashboard-data.json').read_text())
    dates=['2026-11-02','2026-11-03','2026-11-04','2026-11-05','2026-11-06','2026-11-09']
    times=[int(datetime.fromisoformat(d+'T05:30:00+00:00').timestamp()*1000) for d in dates]
    bars=[{'time':t,'price':p} for t,p in zip(times,[100,90,100,100,90,95])]
    ev=[]
    for i,t in enumerate(times[:-1]):
        d=1 if i%2==0 else -1
        ev.append({'id':i+1,'event_key':'synthetic-'+str(i),'unix_ms':t-3600000,'time':datetime.fromtimestamp((t-3600000)/1000,timezone.utc).isoformat(),
            'available_ms':t-60000,'completed_at':datetime.fromtimestamp((t-60000)/1000,timezone.utc).isoformat(),
            'direction':d,'strength':2,'platform':'Facebook' if i%2==0 else 'Threads','target':'模擬標的','summary':'【模擬資料】多單虧損／空單虧損／平手／勝／未平倉驗收，並非真實貼文。',
            'symbol':'0050.TW','proxy':True,'urls':[],'is_flip':True,'sentiment':'【模擬】恐慌' if d==1 else '【模擬】亢奮',
            'media_note':'【模擬】無媒體、未進行任何 AI 判讀','historical':False,'baseline':True,'fetched_at':None})
    data.update(events=ev,market={'fetched_at':None,'series':{'1d':bars,'30m':[]},'errors':[],'symbol':'0050.TW','source':'synthetic'},
        modes={m:simulate(ev,bars if m=='B' else [],m) for m in ('A','B')},
        available_modes={m:simulate(ev,bars if m=='B' else [],m,basis='available') for m in ('A','B')},
        built_at='2026-11-10T05:00:00+00:00',simulation=True)
    return data

def main():
    data=sample();stats=data['modes']['B']['stats']
    assert (stats['settled'],stats['wins'],stats['losses'],stats['ties'],stats['open'])==(4,1,2,1,1)
    assert stats['win_rate']==25
    html=(ROOT/'docs/index.html').read_text().replace('反指標研究室','模擬資料驗收').replace('部分資料績效','模擬資料 · 非真實績效').replace('歷史判讀尚未補齊','本頁全為離線測試資料').replace('讓每一筆訊號，','【模擬資料預覽】')
    html=html.replace('歷史判讀進度','原歷史進度（與模擬事件無關）')
    html=html.replace('<link rel="stylesheet" href="dashboard.css">','<style>'+(ROOT/'docs/dashboard.css').read_text()+'</style>')
    html=html.replace('<script src="dashboard-data.js" defer></script>','').replace('<script src="dashboard.js" defer></script>','')
    text=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
    html=html.replace('</body>','<script>window.INLINE_PREVIEW=true;window.DASHBOARD_DATA='+text+';</script><script>'+(ROOT/'docs/dashboard.js').read_text()+'</script></body>')
    (ROOT/'docs/validation-preview.html').write_text(html)
    report={'simulation':True,'external_apify_requests':0,'external_ai_requests':0,'telegram_send_requests':0,
        'stats':stats,'trades':data['modes']['B']['trades'],'curve':data['modes']['B']['curve'],
        'expected_final_equity':92.8888888888889,'notice':'Synthetic prices and posts, not investment results. Notification failure/crash cases verified in test_live_pipeline.py.'}
    assert abs(report['curve'][-1]['equity']-report['expected_final_equity'])<1e-8
    (ROOT/'data/live_offline_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
