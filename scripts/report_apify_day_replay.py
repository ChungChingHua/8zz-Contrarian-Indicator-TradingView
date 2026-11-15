"""Offline publication of the isolated cost replay; no API or production writes. MPL-2.0."""
import json
import sys
from pathlib import Path
from decimal import Decimal
import apify_day_replay as d


def compare_posts(state, posts):
    findings=[]
    for e in state['runs']:
        if e.get('result_count') is None: continue
        lo=d.datetime.fromisoformat(e['query_start_utc']);hi=d.datetime.fromisoformat(e['query_end_utc'])
        missing=[p['key'] for p in posts.values() if p['source']==e['source'] and
            lo<=d.datetime.fromisoformat(p['published_at'])<hi and p['key'] not in e.get('post_keys',[])]
        if missing:
            findings.append({'round':e['round'],'source':e['source'],'run_id':e.get('id'),
                'query_start_taipei':e['query_start_taipei'],'query_end_taipei':e['query_end_taipei'],
                'missing_previously_or_elsewhere_observed_keys':missing})
            e['offline_possible_missing_keys']=missing
    state['offline_post_return_discrepancies']=findings


def build(state):
    runs=state['runs'];cost=state.get('costs',{});status=state['status']
    done=sum(e.get('status')=='SUCCEEDED' and e.get('result_count') is not None for e in runs)
    lines=['# 2026/11/10 交易日抓取成本：事後重播', '',
        '**這是事後重播成本，不能當成當日即時偵測延遲或資料完整性驗證。**', '',
        f"執行狀態：`{status}`；遠端帳本 `{state['test_id']}`。已保存 Dataset 結果的成功 run：{done}／40；啟動預留：{state['reserved_starts']}／40。", '',
        '實際執行時間（台灣）：'+d.taipei(state['created_at'])+' ～ '+d.taipei(state['updated_at'])+'。', '',
        '模擬 2026/11/10 台灣時間 08:45～13:30，每 15 分鐘一輪、20 輪。首輪獨立基礎游標為 11/9 13:30，實際查詢由 11/9 11:30 開始。後續依各平台上次成功測試游標往前兩小時，到該輪截止時間；受限時不推進。所有時間區間採起點包含、終點不包含。', '',
        '## 成本與用量', '',
        '| 平台 | run 數 | 有效文章回傳數（含重複） | 診斷列 | 重複數 | 首次新增數 | 最新 usageTotalUsd 合計 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for source in d.t.ACTORS:
        entries=[e for e in runs if e['source']==source]
        values=[sum(e.get(k,0) for e in entries) for k in ('valid_posts','diagnostic_rows','duplicates','first_new')]
        lines.append('| '+source+' | '+str(len(entries))+' | '+' | '.join(map(str,values))+' | US$'+cost.get('platform_usd',{}).get(source,'未知')+' |')
    lines += ['', '**全天 API 最新可觀測值：US$'+cost.get('observed_total_usd','未知')+'。**', '',
        '只加總每次 `usageTotalUsd` 一次。`usageUsd` 是分項，計費事件是明細，`externalChargedTotalUsd` 是另一欄位，全部獨立保存、不重複相加。官方文件指出 usageTotalUsd 為 run 總成本，而 externalChargedTotalUsd 僅適用 multi-tenant Standby 對其他使用者的計費；未把它視為本次額外帳單。', '',
        '每個已知 run 完成後都安排一次唯讀刷新；沒有為費用查詢啟動新 run。原始提交／初次完成／最後查詢快照都保存在獨立帳本。若仍有成本缺失或刷新失敗，見下列清單。即使事件計數已對帳，也未獨立核對最終已結算帳單，API 數值仍可能延遲更新，零不代表免費。', '',
        '官方依據：[啟動費用上限](https://docs.apify.com/api/v2/actors-runs-post)、[run 費用定義與完成後可能延遲](https://docs.apify.com/api/v2/actor-run-get)。', '',
        '每月共用啟動帳：'+str(state.get('monthly_runs_before'))+' → '+str(state.get('monthly_runs_after'))+'；帳本原始單次上限：'+str(state.get('cap_usd_per_start'))+' USD，總授權上限：'+str(state.get('maximum_authorized_usd'))+' USD（None 表示未設程式費用上限），不是實際扣款。現行程式已取消每月啟動次數限制。預留在提交前經 GitHub CAS 保存；結果不明不得重送。', '',
        'Apify HTTP 請求：`'+json.dumps(state.get('apify_http_requests',{}))+'`。POST 包括啟動與任何必要的安全中止，實際啟動以各 run 與預留明細為準；本次不進行 AI、Telegram、網站呼叫或媒體辨識。', '',
        '## 每月估算（不是報價或最終帳單）', '',
        '| 交易日數 | 以本次全天 API 成本直接相乘 | 預計 Actor 啟動次數 |', '|---|---:|---:|']
    events={s:{} for s in d.t.ACTORS}
    for e in runs:
        for key,value in e.get('chargedEventCounts',{}).items():
            events[e['source']][key]=events[e['source']].get(key,0)+value
    changed=sum(len(e.get('cost_snapshots',[]))>1 and
        str(e['cost_snapshots'][-1].get('usageTotalUsd'))!=str(e['cost_snapshots'][-2].get('usageTotalUsd')) for e in runs)
    note='費用延遲實測：'+str(changed)+' 次 run 的最後刷新金額不同於初次完成值。計費事件合計為 '+json.dumps(events,ensure_ascii=False)+'。計費事件數不等於有效文章數：Facebook 診斷列也有被計入 post／filter-applied，Threads post 計費事件亦多於有效文章回傳數；不能以文章數替代服務回報費用。'
    index=lines.index('## 每月估算（不是報價或最終帳單）')
    lines[index:index]=[note,'']
    estimates=cost.get('monthly_estimates_usd')
    for n in (20,22,23):
        lines.append('| '+str(n)+' | '+('US$'+estimates[str(n)] if estimates else '未完成全天／成本缺失，無法據此估算')+' | '+str(40*n)+' |')
    lines += ['', '以上僅包含本次核實的抓取 run 成本，不包含 AI、Telegram、網站、匯率／稅、GitHub Actions 或其他未核實成本；文章量、定價、免費方案與延遲結算均可能改變。每天 40 次啟動對應每月 800／880／920 次，現行程式不設每月啟動次數上限，服務端額度與費用仍可能限制執行；此估算不保證可連續執行整月，排程仍關閉。', '',
        '## Actor 與參數', '']
    for source,actor in d.t.ACTORS.items():
        versions=sorted({str(e.get('buildNumber','未取得'))+' (`'+str(e.get('buildId','未取得'))+'`)' for e in runs if e['source']==source})
        lines.append('- '+source+'：`'+actor+'`；實際版本：'+', '.join(versions))
    lines += ['', '沿用正式流程的 input：Facebook startUrls／resultsLimit=50／onlyPostsNewerThan／onlyPostsOlderThan；Threads mode=posts／usernames=[banini31]／maxPosts=50／includeProfile=false／postedAfter／postedBefore。離線測試直接擷取正式 input 分支比對。query 參數 timeout=180、memory=512、maxItems=50；現行不傳 maxTotalChargeUsd，歷史 run 的費用限制以帳本 requested_options／options 為準；restartOnError=false，禁止平台重啟。實際 options、版本與 build ID 都保存於逐 run 帳本；若平台調整實際記憶體，以 options 為準。', '',
        '## 逐輪、逐平台明細', '',
        '全部為台灣時間（UTC+8）。「有效」限指定作者／Threads 明確非回覆非轉貼，且在該實際查詢區間內；「重複／新增」依**本次獨立帳本的平台＋貼文 ID**，不與正式文章帳本比對。相同內容若在兩平台各有 ID，仍分平台計數，不代表跨平台獨立文章總數。其他作者／回覆等排除數與窗外文章另見 JSON／CSV。', '',
        '| 輪 | 截止 | 平台 | 實際查詢起點→終點 | 版本 | run ID | 狀態 | runTimeSecs | 有效 | 診斷 | 重複 | 新增 | US$ | 游標／受限 |',
        '|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    for e in runs:
        times=e['query_start_taipei'][:16].replace('T',' ')+' → '+e['query_end_taipei'][:16].replace('T',' ')
        reasons=e.get('incomplete_reasons',[])
        row=[e['round'],e['simulated_cutoff_taipei'][11:16],e['source'],times,e.get('buildNumber','—'),
            '`'+str(e.get('id','未取得'))+'`',e.get('status'),e.get('duration_seconds','—'),e.get('valid_posts','—'),
            e.get('diagnostic_rows','—'),e.get('duplicates','—'),e.get('first_new','—'),e.get('usageTotalUsd','未知'),
            ('; '.join(reasons) if reasons else '推進')+('；離線比對未回傳 '+str(len(e['offline_possible_missing_keys']))+' 篇' if e.get('offline_possible_missing_keys') else '')]
        lines.append('| '+' | '.join(map(str,row))+' |')
    lines += ['', '## 未完成、受限與可能漏資料', '',
        '不可因 Actor SUCCEEDED 就認定資料完整。50 筆結果、費用達上限／截斷訊息、不明 schema、技術失敗等均標記，測試游標不因此推進。`no_items` 診斷列單獨列數，不當文章；已知 no_items 本身不直接認定失敗。', '',
        '- 不完整 run 時間窗：'+str(len(state.get('incomplete_windows',[]))),
        '- 尚未嘗試的輪／平台：'+str(len(state.get('unattempted',[]))),
        '- 離線比對有回傳差異的時間窗：'+str(len(state.get('offline_post_return_discrepancies',[]))),
        '- 缺失成本：'+json.dumps(cost.get('missing_costs',[])),
        '- 尚未完成最終唯讀費用刷新 run 數：'+str(sum(bool(e.get('id')) and not e.get('final_cost_refreshed',False) for e in runs)),
        '- 停止原因：'+str(state.get('error_code','無')),
        '- 費用刷新異常：'+json.dumps(state.get('billing_refresh_error'),ensure_ascii=False),
        '- 最終測試游標：'+json.dumps({k:d.taipei(v) for k,v in state.get('test_cursors',{}).items()},ensure_ascii=False),'']
    if state.get('offline_post_return_discrepancies'):
        lines += ['離線比對發現下列時間窗未回傳本次其他輪曾取得、且發文時間落在查詢範圍內的文章。這是可能漏資料或回傳不穩定的證據；不能單憑此判定原因或當日是否可取得，也不把 no_items 直接判為抓取失敗。保留當時模擬游標行為，不重跑、不修改正式流程。', '', '```json',json.dumps(state['offline_post_return_discrepancies'],ensure_ascii=False,indent=2),'```','']
    if state.get('incomplete_windows'): lines += ['```json',json.dumps(state['incomplete_windows'],ensure_ascii=False,indent=2),'```','']
    if state.get('unattempted'): lines += ['```json',json.dumps(state['unattempted'],ensure_ascii=False,indent=2),'```','']
    lines += ['## 隔離與證據', '',
        '只讀 Git tree SHA 核對正式資料，沒有讀取正式成功截止時間作為測試游標。正式資料／Pine／通知與正式 workflow 共 '+str(len(state.get('formal_shas_before',{})))+' 檔的前後 blob SHA 比較結果：**'+str(state.get('formal_state_unchanged'))+'**。測試文章、游標、去重、run 與費用使用獨立帳本；共用帳本只更新啟動預留與費用。', '',
        '- [逐輪 CSV](apify-day-replay-20261110-01.csv)',
        '- [獨立遠端進度與費用帳本](../data/cost_tests/apify-day-replay-20261110-01.json)',
        '- [獨立測試文章與去重帳本](../data/cost_tests/apify-day-replay-20261110-01-posts.json)', '',
        '離線驗證：10 項 replay 測試涵蓋 40 次上限、月保護、隔離、費用不重複加總、區間／重疊、無重試、額度停止、受限不推進、延遲費用使游標失效，以及正式 input 相同。未變更情緒規則，沒有重新判讀情緒。完成後停用本次線上測試入口；不啟用正式排程、不發布網站、不合併 PR。','']
    return '\n'.join(lines)


if __name__=='__main__':
    state=json.loads(Path(sys.argv[1]).read_text())
    if len(sys.argv)>2: compare_posts(state,json.loads(Path(sys.argv[2]).read_text()))
    d.write_reports(state,'docs')
    Path('docs/apify-day-replay-20261110-01.md').write_text(build(state))
