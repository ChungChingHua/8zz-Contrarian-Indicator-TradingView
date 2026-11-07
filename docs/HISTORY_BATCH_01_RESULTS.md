# 原作者規則：第一批歷史處理結果

[原作者依據與撤回門檻](ORIGINAL_AUTHOR_RESTORATION.md)。本批只用同篇原文及真正附圖，沒有外部上下文、留言、未來貼文或後續行情。

## 統計口徑

```json
{
  "selected": 5,
  "successful_valid_responses": 5,
  "signals": 2,
  "no_signal": 2,
  "pending_confirmation": 1,
  "technical_failure": 0,
  "unknown": 0,
  "not_started_in_batch": 0,
  "remaining_not_started_groups": 643,
  "generation_attempts_reserved": 5,
  "known_http_responses": 5,
  "supplied_images": 1,
  "unavailable_images": 2,
  "unanalysed_videos": 1,
  "recovered_input_failures": 1,
  "reconciled_local_validation_failures": 1,
  "model_queries": 0,
  "other_provider_queries": 0,
  "actual_points_deducted": null,
  "service_reported_usage": {
    "input_tokens": 13016,
    "output_tokens": 706,
    "total_tokens": 13722,
    "reasoning_tokens": 0
  }
}
```

成功是取得符合固定格式的回應，包含有訊號／無訊號／待確認三類，不能再與三類相加。技術失敗包含媒體前檢失敗（可能0次生成）；unknown是可能已送出但未保存結果，不自動重送。剩餘未開始群組以本批凍結的eligible_groups減已開始紀錄，另列待確認／技術失敗／unknown，不把它們混成可自動重試。

原archive 659篇，先前測試／處理排除11篇，當時可開始648群組；本批原文不相同，已保守去重，未把不同媒體的同文誤合併。確定無關保存completed_no_signal，未來選取讀帳本排除，不重送。

本批generation_attempts_reserved在遠端ACK前即預留，含未知情況的保守上限；若每次都有HTTP回應則可確認本批請求次數。模型清單／額度查詢均0，沒有Apify重抓。媒體下載不計生成。

## 逐篇

### 1. facebook 1604315791053010

[來源](https://www.facebook.com/DieWithoutBang/posts/pfbid02LQQGfGWXtavebbw24Umq6352tvhCPipioki6cqYZQr3bH8ZztRNY7D8q3K6VUAfrl) · 2026-07-20T08:32:36+08:00（Asia/Taipei）

原文：

> 看什麼看
> 今天就是反彈啦～
> 妥妥開高走低
>
> 今天繼續看有什麼可以賣的轉去傳產⋯

狀態：**completed_signal**；生成預留／嘗試 1；HTTP 200。

方向 -1／強度 2；action：賣出/尋找賣點；ticker：空白／未取得。

依據：語氣偏自信/尋求賣出機會（『看有什麼可以賣的轉去傳產』），屬於主動找賣點的樂觀/亢奮傾向，偏空。

標的來源註記：

使用上下文：僅同篇，context=[]；作者原few-shot是判讀規則，不是本批預設答案。

媒體範圍：{"analysis_scope": "text_only_images_unavailable", "unanalysed_media": [{"attachment_index": 0, "kind": "image", "status": "圖片未分析", "error_type": "OSError", "errno": 101, "reason": "network_unreachable"}], "media_failures": [{"attachment_index": 0, "kind": "image", "status": "圖片未分析", "error_type": "OSError", "errno": 101, "reason": "network_unreachable"}], "images_supplied": 0, "image_evidence": [], "human_image_verified": false, "source_note": "Only actual supplied images were read. Unavailable images/video not analysed; if visible text is insufficient, use pending_confirmation under original ambiguous-post rule."}

圖像轉錄／觀察（服務聲稱，未人工核圖）：[]

未分析圖片註記（不當作實際圖像觀察）：[{"image_index": 0, "visible_text": "", "observation": "貼文標記有一張圖片但未提供/無法分析（network_unreachable）", "readable": false}]

委託強度booster實際命中片語：[]；AI原強度：2

靜態代碼校正（不改情緒）：null

服務回報模型、推理與token：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2628, "input_tokens": 2457, "output_tokens": 171, "reasoning_tokens": 0}}

原回應保存於遠端帳本raw_response，處理後結果為processed；只有原作者委託證據booster可改強度，不以ticker／人工核圖／情緒regex否決方向。

### 2. threads 3945193370117864190

[來源](https://www.threads.com/@banini31/post/DbAJHe0Gfr-) · 2026-07-20T13:02:00+08:00（Asia/Taipei）

原文：

> so weak...😭😭😭😭

狀態：**completed_signal**；生成預留／嘗試 1；HTTP 200。

方向 1／強度 3；action：未知(可能被套)；ticker：6505.TW。

依據：貼文文字情緒悲傷加上附上即時盤面截圖（顯示下跌/買進價格），發文者處於被套/痛苦情緒，偏多訊號；且圖片含有委託/成交介面證據，強度設為3。

標的來源註記：根據圖中標的與畫面顯示，對應yfinance代碼為6505.TWO（台塑化）。

使用上下文：僅同篇，context=[]；作者原few-shot是判讀規則，不是本批預設答案。

媒體範圍：{"analysis_scope": "text_and_images", "unanalysed_media": [], "media_failures": [], "images_supplied": 1, "image_evidence": [{"sha256": "6dd4418c628c74641ff4da95c4fac0365ba74f3c614ca7e367dd2d39707f374c", "bytes": 98546, "mime": "image/jpeg", "attachment_index": 0}], "human_image_verified": false, "source_note": "Only actual supplied images were read. Unavailable images/video not analysed; if visible text is insufficient, use pending_confirmation under original ambiguous-post rule."}

圖像轉錄／觀察（服務聲稱，未人工核圖）：[{"image_index": 0, "visible_text": "台塑化 78.50 買進 78.50 賣出 78.60 07/20 13:01:40 6505", "observation": "截圖為台塑化盤中走勢圖、即時買賣價格與時間，顯示股價由84.30降至78.40，情緒負面（so weak）。", "readable": true}]

未分析圖片註記（不當作實際圖像觀察）：[]

委託強度booster實際命中片語：[]；AI原強度：3

靜態代碼校正（不改情緒）：{"issuer_code": "6505", "issuer_name": "台塑石化股份有限公司", "issuer_shortname": "台塑化", "venue": "TWSE", "listing_date": "2003-12-26", "incorrect_suffix_candidate": "6505.TWO", "yfinance_ticker": "6505.TW", "source_url": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L", "reference_sha256": "4ffd2c0eacf8ce1baf64bbeafc501270f69fed6c7523f6e168bb9232932424f1", "sentiment_unchanged": true}

服務回報模型、推理與token：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 3458, "input_tokens": 3203, "output_tokens": 255, "reasoning_tokens": 0}}

原回應保存於遠端帳本raw_response，處理後結果為processed；只有原作者委託證據booster可改強度，不以ticker／人工核圖／情緒regex否決方向。

### 3. threads 3945215061657207424

[來源](https://www.threads.com/@banini31/post/DbAODIomUKA) · 2026-07-20T13:45:06+08:00（Asia/Taipei）

原文：

> @meta.ai  請問從台北101頂部往下墜落要多久的時間，只是好奇

狀態：**completed_no_signal**；生成預留／嘗試 1；HTTP 200。

方向 0／強度 1；action：；ticker：空白／未取得。

依據：與投資無關的好奇詢問，沒有表達持倉或交易情緒

標的來源註記：

使用上下文：僅同篇，context=[]；作者原few-shot是判讀規則，不是本批預設答案。

媒體範圍：{"analysis_scope": "text_only_no_attachments", "unanalysed_media": [], "media_failures": [], "images_supplied": 0, "image_evidence": [], "human_image_verified": false, "source_note": "Only actual supplied images were read. Unavailable images/video not analysed; if visible text is insufficient, use pending_confirmation under original ambiguous-post rule."}

圖像轉錄／觀察（服務聲稱，未人工核圖）：[]

未分析圖片註記（不當作實際圖像觀察）：[]

委託強度booster實際命中片語：[]；AI原強度：1

靜態代碼校正（不改情緒）：null

服務回報模型、推理與token：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2429, "input_tokens": 2355, "output_tokens": 74, "reasoning_tokens": 0}}

原回應保存於遠端帳本raw_response，處理後結果為processed；只有原作者委託證據booster可改強度，不以ticker／人工核圖／情緒regex否決方向。

### 4. threads 3945363065667705968

[來源](https://www.threads.com/@banini31/post/DbAvs4HEdxw) · 2026-07-20T18:41:00+08:00（Asia/Taipei）

原文：

> 每次都忘記發脆
> 二話不說！乾爹又來了這次是
> 小日子法式水果店～little sunday❤️
>
> 本次試團購業配（ya~~)
> 果乾系列可以選擇的有（以甜度排序）
> 白桃>蘋果>奇異果>鳳梨>芭樂>蔬果（鹹）
>
> 而且還有搭配獎金活動❤️ 
> 如果團購總金額有機會破100萬的話
> 居然會抽獎送給一名幸運的購買者！？ 
>
> 獎金的金額居然是開獎日當天等值一張群創股價
> （乾爹是不是被套在70啊，太可憐了，還好我才套在60）
>
> 這邊是這次的團購連結：
> https://littlesunday-fruits.my1shop.com/banini

狀態：**completed_no_signal**；生成預留／嘗試 1；HTTP 200。

方向 0／強度 1；action：；ticker：空白／未取得。

依據：業配/團購宣傳與生活內容，雖提到被套但非明確表達個人投資動作或情緒立場，屬活動/廣告性質，跳過。

標的來源註記：

使用上下文：僅同篇，context=[]；作者原few-shot是判讀規則，不是本批預設答案。

媒體範圍：{"analysis_scope": "text_only_video_unanalysed", "unanalysed_media": [{"attachment_index": 0, "kind": "video", "status": "影片未分析"}], "media_failures": [], "images_supplied": 0, "image_evidence": [], "human_image_verified": false, "source_note": "Only actual supplied images were read. Unavailable images/video not analysed; if visible text is insufficient, use pending_confirmation under original ambiguous-post rule."}

圖像轉錄／觀察（服務聲稱，未人工核圖）：[]

未分析圖片註記（不當作實際圖像觀察）：[]

委託強度booster實際命中片語：[]；AI原強度：1

靜態代碼校正（不改情緒）：null

服務回報模型、推理與token：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2676, "input_tokens": 2576, "output_tokens": 100, "reasoning_tokens": 0}}

原回應保存於遠端帳本raw_response，處理後結果為processed；只有原作者委託證據booster可改強度，不以ticker／人工核圖／情緒regex否決方向。

### 5. facebook 1604744667676789

[來源](https://www.facebook.com/DieWithoutBang/posts/pfbid033QtWmAt8rSXVRvNhxaRtYTvHeqnWrXBTsZDyS5oRJ4wFJbzaLesrzYN8PGPQpdyBl) · 2026-07-20T21:10:06+08:00（Asia/Taipei）

原文：

> 是時候教韓國人做股票了

狀態：**pending_confirmation**；生成預留／嘗試 1；HTTP 200。

方向 0／強度 1；action：；ticker：空白／未取得。

依據：發文內容短促且無明確表達個人投資立場或情緒（玩笑/挑釁語氣），且圖片無法分析，依規則對不確定投資關聯的貼文跳過。

標的來源註記：

使用上下文：僅同篇，context=[]；作者原few-shot是判讀規則，不是本批預設答案。

媒體範圍：{"analysis_scope": "text_only_images_unavailable", "unanalysed_media": [{"attachment_index": 0, "kind": "image", "status": "圖片未分析", "error_type": "OSError", "errno": 101, "reason": "network_unreachable"}], "media_failures": [{"attachment_index": 0, "kind": "image", "status": "圖片未分析", "error_type": "OSError", "errno": 101, "reason": "network_unreachable"}], "images_supplied": 0, "image_evidence": [], "human_image_verified": false, "source_note": "Only actual supplied images were read. Unavailable images/video not analysed; if visible text is insufficient, use pending_confirmation under original ambiguous-post rule."}

圖像轉錄／觀察（服務聲稱，未人工核圖）：[]

未分析圖片註記（不當作實際圖像觀察）：[]

委託強度booster實際命中片語：[]；AI原強度：1

靜態代碼校正（不改情緒）：null

服務回報模型、推理與token：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2531, "input_tokens": 2425, "output_tokens": 106, "reasoning_tokens": 0}}

原回應保存於遠端帳本raw_response，處理後結果為processed；只有原作者委託證據booster可改強度，不以ticker／人工核圖／情緒regex否決方向。

## 用量、費用及候選Pine

請求設定為ChatAnywhere https://api.chatanywhere.tech/v1，gpt-5-mini／minimal／strict schema。模型、推理與usage均為服務回報，未獨立驗證底層模型或實際推理；reasoning_tokens=0若有回傳也只是服務數字。

服務usage加總：{"input_tokens": 13016, "output_tokens": 706, "total_tokens": 13722, "reasoning_tokens": 0}

前後免費點數、剩餘請求額度及實際扣點：{"quota_before": null, "quota_after": null, "actual_points_deducted": null}。缺值就是未知，可能延遲；未查帳單，不宣稱零扣點，不把點數當tokens，不以tokens估算實際扣點。

[完整候選Pine](../candidates/8zz-original-author-batch-01.pine)；結構檢查：{"historical_events": 150, "added_events": 2, "total_events": 152, "historical_blocks_preserved": true, "historical_neutral_events_preserved": 1, "new_events_nonzero": true, "arrays_paired": true, "timestamps_ordered": true, "directions_strengths_valid": true, "tradingview_compiled": false}

初始媒體失敗與本地過嚴圖片註記檢查均已保留歷史，修復過程沒有重送第一筆；最終post狀態technical_failure=0不代表從未遇過技術問題。媒體未讀取2張另列，不冒充API全媒體成功。

保留歷史所有事件與作者署名／MPL-2.0，待確認、技術失敗、unknown無箭頭。這是候選檔，未覆寫正式8zz-indicator.pine或archive，也未發布Pages。未在TradingView編譯，不能宣稱編譯通過。

TradingView手動步驟：備份原腳本 → 開啟候選Pine的Raw全文 → Pine Editor完整取代 → 儲存並加入／更新圖表 → 檢查編譯、日期、箭頭及強度；如需套用既有提醒，刪除並依新版重建。GitHub更新不會自動同步TradingView。

遠端進度：data/history_progress/original-author-20261107-01.json。相同batch手動再啟動只復核／恢復允許的未開始項；finished／stopped或unknown不會產生新請求。繼續另一批需另行授權，不啟用持續排程、不合併PR。

## 本輪實際檢查與保留疑點

- [首段執行](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42354590261)：媒體前檢失敗，0生成，已遠端保存。
- [無金鑰診斷](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42365658302)：CDN僅IPv6、errno101；沒有生成。
- [恢復未送出資料](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42366144151)：第一筆HTTP200生成1次，誠實未讀圖片註記被舊本地數量檢查拒絕，原JSON完整保存。
- [離線重驗後續未開始4篇](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42366512318)：首筆不重送，續4次，最終遠端帳本finished=true、總5次、每篇1次。原始回應hash與修正歷史可稽核。

125項離線測試與Python編譯檢查通過；恢復、stale CAS、quota、格式錯誤、送出後中斷、結果提交失敗、unknown禁止重送均已模擬。Pine只做結構檢查，未實際TradingView編譯。

第2筆圖像轉錄含6505／台塑化。服務回傳6505.TWO，但[證交所公開公司資料](https://openapi.twse.com.tw/v1/opendata/t187ap03_L)列台塑化於2003-12-26上市（TWSE），因此僅校正yfinance市場後綴為6505.TW；原服務ticker仍留raw及original_ai_ticker，靜態參照與hash另存data/static_ticker_reference.json。查核沒有取得後續價格，也沒有回灌情緒；方向+1與強度3未改。PR最新候選檔包含此靜態資料修正，早先Actions artifact是執行當時版本，使用前應取PR最新檔。

服務對第2筆理由提到「委託／成交介面」，但其實際轉錄沒有原作者強制booster片語；本地order_proof_rule_matched=false，**保留的是AI原評強度3，不宣稱已證明真實成交**。原規則允許非委託的極端情緒評3，不能反過來增設「沒成交文字不得評3」的新門檻。圖像與情緒解讀仍是服務回報，候選供檢查，不是準確性或交易績效保證。

本輪模型清單／帳號餘額查詢0；另做不帶金鑰的公開DNS、來源照片頁與證交所靜態資料查核，不屬生成，也不把這些控制／參照請求混進5次模型請求。沒有重新付費抓Apify歷史。

## 手動入口與停止狀態

Actions → **Original-author history batch (manual)** → Run workflow → 選PR分支`codex/social-pipeline-20261106`。現在固定batch已finished、5次授權耗盡，預設再啟動只讀帳本，不會再生成。恢復選項預設false；只有程式中嚴格限定的零生成或已保存HTTP200本地校正狀態能使用，不能重試API／額度錯誤或unknown。新批次需另行授權並固定新計畫，不能改ID繞過。

已移除臨時push觸發，不啟用schedule或Pages，不合併PR。舊smoke／品質入口仍停用，一般pause=true。正式archive與正式8zz-indicator.pine不變，交付完整候選152事件（歷史150＋本批2）；待確認那篇沒有新箭頭。

