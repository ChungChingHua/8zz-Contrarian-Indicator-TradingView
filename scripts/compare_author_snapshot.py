"""Offline comparison against captured public author snapshot; never rewrites site data."""
import json,hashlib,math
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from build_audited_dashboard import simulate
from futures_performance import simulate_futures
ROOT=Path(__file__).resolve().parent.parent
TZ=ZoneInfo('Asia/Taipei')
def normalize(events):
    out=[];direction=0
    for i,event in enumerate(sorted(events,key=lambda e:e['unix_ms']),1):
        row=dict(event,id=i,is_flip=bool(event['direction'] and event['direction']!=direction));out.append(row)
        if event['direction']:direction=event['direction']
    return out

def calculate():
    ap=ROOT/'data/comparisons/author-20260720-events.json';author=json.loads(ap.read_text())
    ours=json.loads((ROOT/'docs/dashboard-data.json').read_text())
    cutoff=datetime.fromisoformat(author['stats']['generated_at']);limit=int(cutoff.timestamp()*1000)
    result={'cutoff_utc':cutoff.isoformat(),'cutoff_taipei':cutoff.astimezone(TZ).isoformat(),
            'author_url':'https://hansai-art.github.io/8zz-Contrarian-Indicator-TradingView/events.json',
            'author_snapshot_sha256':hashlib.sha256(ap.read_bytes()).hexdigest(),
            'author_source_sha256':hashlib.sha256((ROOT/'data/comparisons/author-build-site-data-source.txt').read_bytes()).hexdigest(),
            'local_snapshot_sha256':hashlib.sha256((ROOT/'docs/dashboard-data.json').read_bytes()).hexdigest(),
            'author_reconciliation':{},'comparisons':[],'limitations':[
                'Historical publication-time research only; judgments may have been completed later.',
                'Uses saved Shioaji history retrieved later, not an immutable market-data archive captured on 2026-07-20.',
                'Author snapshot has rounded per-event PnL and no full raw quote/portfolio ledger.',
                'Author curves end July 16 (A) and July 7 (B), not full July 20 mark-to-market; local curves include open PnL.',
                'Mixed individual tickers and overlapping author trades differ from single 0050 or TXFR1 nominal-capital proxy.',
                'TXFR1 settlement-week/cross-roll exclusions remain; not a complete futures execution/roll simulation.']}
    for mode in ('A','B'):
        pnl='pnl_pct_a' if mode=='A' else 'pnl_pct';outcome='outcome_a' if mode=='A' else 'outcome';exit_key='exit_date_a' if mode=='A' else 'exit_date'
        flips=[e for e in author['events'] if e['is_flip']]
        closed=[e for e in flips if e.get(outcome) in ('win','loss','flat') and e.get(pnl) is not None]
        signs=Counter('wins' if e[pnl]>0 else 'losses' if e[pnl]<0 else 'ties' for e in closed)
        mis=[{'date':e['date'],'ticker':e['ticker'],'pnl_pct':e[pnl],'outcome':e[outcome]} for e in closed if e[pnl]<0 and e[outcome]!='loss']
        stats=author['stats']['mode_'+mode.lower()];curve=author['equity_curves']['mode_'+mode.lower()]
        recomputed=100*math.prod(1+e[pnl]/100 for e in closed)
        assert abs(recomputed-curve[-1]['value'])<0.011
        denominator=stats['wins']+stats['losses']+stats['open_flips']
        assert round(stats['wins']/denominator*100,1)==stats['win_rate']
        overlaps=[]
        for i,event in enumerate(closed):
            previous=next((a for a in closed[:i] if a['entry_date'][:10]<event['entry_date'][:10]<a[exit_key][:10]),None)
            if previous:overlaps.append({'earlier_entry':previous['entry_date'],'earlier_exit':previous[exit_key],'earlier_ticker':previous['ticker'],'later_entry':event['entry_date'],'later_ticker':event['ticker']})
        result['author_reconciliation'][mode]={'reported':stats,'numeric_pnl_counts':dict(signs),
          'strict_closed_win_rate':signs['wins']/len(closed)*100,'closed_count':len(closed),
          'reported_denominator_wins_losses_open':denominator,
          'negative_pnl_mislabeled_count':len(mis),'negative_pnl_mislabeled':mis,
          'mean_closed_pnl':sum(e[pnl] for e in closed)/len(closed),
          'curve_final_date':curve[-1]['date'],'curve_final_nav':curve[-1]['value'],
          'curve_reported_return_pct':curve[-1]['value']-100,'reproduced_nav':recomputed,
          'daily_exit_count':sum(len(e[exit_key])==10 for e in closed),
          'minimum_overlapping_entry_count':len(overlaps),'overlap_examples':overlaps[:4]}
    event_sets={'local_saved_events':normalize([e for e in ours['events'] if e['unix_ms']<=limit]),
                'author_149_events':normalize([e for e in author['events'] if e['unix_ms']<=limit])}
    for sample,events in event_sets.items():
        for asset,item,engine in [('0050',ours,simulate),('TXFR1',ours['instruments']['TXF'],simulate_futures)]:
            bars=[b for b in item['market']['series']['30m'] if b['time']<=limit]
            for mode in ('A','B'):
                model=engine(events,bars,mode,ours['hold_bars'])
                assert all(p['time']<=limit for p in model['curve'])
                assert all(t['entry']['time']<=limit and (not t['exit'] or t['exit']['time']<=limit) for t in model['trades'])
                final=model['curve'][-1]['equity'] if model['curve'] else None
                closed_capital=100*math.prod(1+t['pnl']/100 for t in model['trades'] if t['exit'])
                result['comparisons'].append({'event_set':sample,'events':len(events),'asset':asset,'mode':mode,'stats':model['stats'],'nav_including_open':final,'return_including_open_pct':None if final is None else final-100,'realized_only_nav':closed_capital,'last_bar_taipei':datetime.fromtimestamp(bars[-1]['time']/1000,TZ).isoformat(),'rows':model['rows'],'trades':model['trades']})
    return result

def write(result):
    (ROOT/'data/comparisons/author-20260720-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=['# 原作者最後更新時點績效核對','',f"截止：**{result['cutoff_taipei']}（台北）**。原作者公開資料149事件；我們同截止保存152事件。本報告不改網站、不呼叫AI、Apify、行情API或通知。",'',
      '## 原作者公開快照：勝率與曲線重算','',
      '| 模式 | 網站勝率 | 按逐筆損益重算勝率 | 實際勝／敗／平 | 平均交易報酬 | 快照曲線報酬 |',
      '|---|---:|---:|---:|---:|---:|']
    for mode,r in result['author_reconciliation'].items():
        c=r['numeric_pnl_counts'];lines.append(f"| {mode} | {r['reported']['win_rate']:.1f}% | {r['strict_closed_win_rate']:.2f}% | {c.get('wins',0)}／{c.get('losses',0)}／{c.get('ties',0)} | {r['mean_closed_pnl']:+.2f}% | {r['curve_reported_return_pct']:+.2f}% |")
    lines+=['','原作者B的75.9%＝41÷(41勝＋10敗＋3未平倉)，排除18個flat；其中11筆其實為負報酬。按公開逐筆數字重算為41勝、21敗、7平，41÷69＝59.42%。A的68.2%＝45÷(45＋18＋3)，6筆負報酬被列flat；按逐筆數字為45勝、24敗，45÷69＝65.22%。這裡重算依已四捨五入的公開損益，不是取得其原始成交帳本。','',
      '平均交易報酬仍可由逐筆數字重現（B +0.40%、A +2.06%），分類錯誤主要改變勝率。曲線B100→96.86（-3.14%），A100→277.19（+177.19%），均可用保存逐筆報酬相乘重現；高勝率不等於帳戶獲利。','',
      '## 為何A曲線不能直接當作相同策略帳戶報酬','',
      '- 標的不同：原作者依各事件ticker交易（台美個股、ETF、白銀、原油等），我們選單是單一0050或台指日盤代理。','- 週期不同：原作者程式依進場key解析度取17根，會退回日線或小時線。69筆A結算中30筆出場僅有日期；例如2337.TW於2026/1/22進、2/26出、+45.37%，不是持有17根30分鐘線。','- 原作者優先向發文前搜尋已完成行情，無分鐘資料又會向後找日線；我們只在發文後有效30分鐘棒成交。','- 原作者有重疊交易：A至少66筆進場與另一筆更早進場且未出場交易在不同日重疊，B至少16筆；公開曲線將各筆完整報酬依序複利，未見共用本金分配或資金占用帳本，不能直接解讀為單一資金帳戶。','- 參數歷史選擇：原作者有14～50根的敏感度計算，17根是固定選用值；本次取得的公開資料未提供獨立樣本外驗證，不能據此推論未來績效。','',
      '## 我們保存事件：回推到同一更新時間','',
      '| 標的 | 模式 | 已結算 | 勝／敗／平 | 勝率 | 平均交易報酬 | 含浮動帳戶報酬 |',
      '|---|---|---:|---:|---:|---:|---:|']
    for row in result['comparisons']:
        if row['event_set']!='local_saved_events':continue
        s=row['stats'];lines.append(f"| {row['asset']} | {row['mode']} | {s['settled']} | {s['wins']}／{s['losses']}／{s['ties']} | {s['win_rate']:.2f}% | {s['average']:+.2f}% | {row['return_including_open_pct']:+.2f}% |")
    lines+=['','使用網站現行規則：A/B共用30分鐘進場，A持有17棒且不重疊，B等反向；台指只計日盤並排除結算週及跨轉倉交易。計算只使用截止前事件與已完成行情，沒有用9月底的出場結果回填。每組仍有1筆未平倉，含浮動帳戶報酬與已結算平均報酬是不同指標。','',
      '## 控制事件範圍：改用原作者同149事件','',
      '| 標的 | 模式 | 已結算 | 勝率 | 平均交易報酬 | 含浮動帳戶報酬 |',
      '|---|---|---:|---:|---:|---:|']
    for row in result['comparisons']:
        if row['event_set']!='author_149_events':continue
        s=row['stats'];lines.append(f"| {row['asset']} | {row['mode']} | {s['settled']} | {s['win_rate']:.2f}% | {s['average']:+.2f}% | {row['return_including_open_pct']:+.2f}% |")
    lines+=['','## 限制與核對方法','',
      '- 原作者快照產生時間為7/20 10:15，但A曲線最後點為7/16、B為7/7，基準為7/17；未平倉沒有完整市值資料。因此原作者曲線終值不是可核對的7/20完整帳戶市值。','- 我們最後可用30分鐘行情：0050為7/20 10:00，台指為7/20 10:15（台北）。','- 我們152筆與原作者149筆並非完全同一事件集合；控制149筆的結果另列，不能把差異都歸因於勝率算法。','- 本次用後來保存的歷史行情回推，不是當日凍結的行情快照；也是假設依發文時間已知訊號的歷史參考，不是當時已完成AI判讀的實際交易成績。','- 沒有原作者完整逐筆原始行情、資金帳本與當時所有程式版本，不能宣稱完全獨立驗證其原始成交或回復完整當時帳戶。','',
      '來源：[原作者events.json]('+result['author_url']+')、[原作者計算程式](https://github.com/hansai-art/8zz-Contrarian-Indicator-TradingView/blob/main/scripts/build_site_data.py)。保存來源與SHA-256、逐筆異常、重疊範例、截止測試及完整8組結果在data/comparisons/author-20260720-comparison.json。','',
      '重現：`python scripts/compare_author_snapshot.py`（只讀保存來源，不連外）。']
    (ROOT/'docs/AUTHOR_ASOF_COMPARISON.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    r=calculate();write(r)
    print(json.dumps({'cutoff':r['cutoff_taipei'],'cases':len(r['comparisons']),'future_bars_used':0,'live_site_changed':False},ensure_ascii=False))
