"""Offline report from remotely acknowledged ledger, never calls provider. MPL-2.0."""
import json
from collections import Counter
from pathlib import Path
from history_worker import ROOT,LOCAL
from history_plan import PLAN
from original_candidate import build,OUT

def main():
    ledger=json.loads(LOCAL.read_text());plan=json.loads(PLAN.read_text())
    counts=Counter(r['status'] for r in ledger['records'])
    started=sum(r['status']!='not_started' for r in ledger['records'])
    successful=sum(counts[x] for x in ('completed_signal','completed_no_signal','pending_confirmation'))
    stats={'selected':len(ledger['records']),'successful_valid_responses':successful,'signals':counts['completed_signal'],'no_signal':counts['completed_no_signal'],
       'pending_confirmation':counts['pending_confirmation'],'technical_failure':counts['technical_failure']+counts['input_failure'],'unknown':counts['unknown'],
       'not_started_in_batch':counts['not_started'],'remaining_not_started_groups':plan['selection_stats']['eligible_groups']-started,
       'generation_attempts_reserved':ledger['reserved_generation_attempts'],'known_http_responses':sum('http_status' in r for r in ledger['records']),
       'supplied_images':sum(r.get('media_scope',{}).get('images_supplied',0) for r in ledger['records']),
       'unavailable_images':sum(len(r.get('media_scope',{}).get('media_failures',[])) for r in ledger['records']),
       'unanalysed_videos':sum(m.get('kind')=='video' for r in ledger['records'] for m in r.get('media_scope',{}).get('unanalysed_media',[])),
       'recovered_input_failures':sum(len(r.get('input_failure_history',[])) for r in ledger['records']),
       'reconciled_local_validation_failures':sum(len(r.get('local_validation_history',[])) for r in ledger['records']),
       'model_queries':0,'other_provider_queries':0,'actual_points_deducted':ledger.get('actual_points_deducted')}
    usage={k:sum(r.get('service_response',{}).get('usage',{}).get(k,0) for r in ledger['records']) for k in ('input_tokens','output_tokens','total_tokens','reasoning_tokens')}
    stats['service_reported_usage']=usage
    pine,pine_stats=build(ledger);OUT.parent.mkdir(exist_ok=True);OUT.write_text(pine)
    OUT.with_suffix('.checks.json').write_text(json.dumps(pine_stats,indent=2)+'\n')
    (ROOT/'data/history_batch_01_summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
    lines=['# 原作者規則：第一批歷史處理結果','',
       '[原作者依據與撤回門檻](ORIGINAL_AUTHOR_RESTORATION.md)。本批只用同篇原文及真正附圖，沒有外部上下文、留言、未來貼文或後續行情。', '',
       '## 統計口徑','',json.dumps(stats,ensure_ascii=False,indent=2).join(['```json\n','\n```']), '',
       '成功是取得符合固定格式的回應，包含有訊號／無訊號／待確認三類，不能再與三類相加。技術失敗包含媒體前檢失敗（可能0次生成）；unknown是可能已送出但未保存結果，不自動重送。剩餘未開始群組以本批凍結的eligible_groups減已開始紀錄，另列待確認／技術失敗／unknown，不把它們混成可自動重試。', '',
       f"原archive {plan['selection_stats']['total_posts']}篇，先前測試／處理排除{plan['selection_stats']['excluded_posts']}篇，當時可開始{plan['selection_stats']['eligible_groups']}群組；本批原文不相同，已保守去重，未把不同媒體的同文誤合併。確定無關保存completed_no_signal，未來選取讀帳本排除，不重送。", '',
       '本批generation_attempts_reserved在遠端ACK前即預留，含未知情況的保守上限；若每次都有HTTP回應則可確認本批請求次數。模型清單／額度查詢均0，沒有Apify重抓。媒體下載不計生成。', '',
       '## 逐篇','']
    for r in ledger['records']:
        a=r.get('processed',{});media=r.get('media_scope',{})
        lines+=[f"### {r['number']}. {r['source']} {r['post_id']}",'',f"[來源]({r['url']}) · {r['display_time']}（Asia/Taipei）",'',
          '原文：','']+['> '+x if x else '>' for x in r['text'].splitlines()]
        lines+=['',f"狀態：**{r['status']}**；生成預留／嘗試 {r['attempts']}；HTTP {r.get('http_status')}。",'',
          f"方向 {a.get('direction','未取得')}／強度 {a.get('strength','未取得')}；action：{a.get('action','未取得')}；ticker：{a.get('ticker') or '空白／未取得'}。",'',
          '依據：'+(a.get('reasoning') or r.get('reason','尚未開始')),'',
          '標的來源註記：'+a.get('target_notes','未取得'),'',
          '使用上下文：僅同篇，context=[]；作者原few-shot是判讀規則，不是本批預設答案。','',
          '媒體範圍：'+json.dumps(media,ensure_ascii=False),'',
          '圖像轉錄／觀察（服務聲稱，未人工核圖）：'+json.dumps(a.get('images',[]),ensure_ascii=False),'',
          '未分析圖片註記（不當作實際圖像觀察）：'+json.dumps(a.get('unanalysed_image_notes',[]),ensure_ascii=False),'',
          '委託強度booster實際命中片語：'+json.dumps(a.get('order_proof_phrases_present',[]),ensure_ascii=False)+'；AI原強度：'+str(a.get('original_ai_strength')),'',
          '靜態代碼校正（不改情緒）：'+json.dumps(a.get('ticker_reference_correction'),ensure_ascii=False),'',
          '服務回報模型、推理與token：'+json.dumps(r.get('service_response'),ensure_ascii=False),'',
          '原回應保存於遠端帳本raw_response，處理後結果為processed；只有原作者委託證據booster可改強度，不以ticker／人工核圖／情緒regex否決方向。','']
    lines+=['## 用量、費用及候選Pine','',
       '請求設定為ChatAnywhere https://api.chatanywhere.tech/v1，gpt-5-mini／minimal／strict schema。模型、推理與usage均為服務回報，未獨立驗證底層模型或實際推理；reasoning_tokens=0若有回傳也只是服務數字。','',
       '服務usage加總：'+json.dumps(usage,ensure_ascii=False),'',
       '前後免費點數、剩餘請求額度及實際扣點：'+json.dumps({k:ledger.get(k) for k in ('quota_before','quota_after','actual_points_deducted')},ensure_ascii=False)+'。缺值就是未知，可能延遲；未查帳單，不宣稱零扣點，不把點數當tokens，不以tokens估算實際扣點。','',
       '[完整候選Pine](../candidates/8zz-original-author-batch-01.pine)；結構檢查：'+json.dumps(pine_stats,ensure_ascii=False), '',
       '初始媒體失敗與本地過嚴圖片註記檢查均已保留歷史，修復過程沒有重送第一筆；最終post狀態technical_failure=0不代表從未遇過技術問題。媒體未讀取2張另列，不冒充API全媒體成功。','',
       '保留歷史所有事件與作者署名／MPL-2.0，待確認、技術失敗、unknown無箭頭。這是候選檔，未覆寫正式8zz-indicator.pine或archive，也未發布Pages。未在TradingView編譯，不能宣稱編譯通過。','',
       'TradingView手動步驟：備份原腳本 → 開啟候選Pine的Raw全文 → Pine Editor完整取代 → 儲存並加入／更新圖表 → 檢查編譯、日期、箭頭及強度；如需套用既有提醒，刪除並依新版重建。GitHub更新不會自動同步TradingView。','',
       '遠端進度：data/history_progress/original-author-20261107-01.json。相同batch手動再啟動只復核／恢復允許的未開始項；finished／stopped或unknown不會產生新請求。繼續另一批需另行授權，不啟用持續排程、不合併PR。','']
    audit=ROOT/'docs/HISTORY_BATCH_01_AUDIT.md'
    (ROOT/'docs/HISTORY_BATCH_01_RESULTS.md').write_text('\n'.join(lines)+('\n'+audit.read_text() if audit.exists() else ''))
    print(json.dumps(stats,ensure_ascii=False));print(json.dumps(pine_stats))
if __name__=='__main__':main()
