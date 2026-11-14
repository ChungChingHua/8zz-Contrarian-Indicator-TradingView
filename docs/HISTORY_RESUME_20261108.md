# 2026/11/8 免費額度恢復後續跑結果

本次已依授權持續執行，直到 ChatAnywhere 再次以 HTTP 429 明確表示共用 24 小時 100 次免費請求已耗盡而停止。**歷史尚未補齊**。沒有重試生成、切換模型／供應商／付費服務、啟用排程、發布 Pages 或合併 PR。

資料抓取截止仍為台北時間 **2026-11-07 20:15:59**，封存共 666 篇；本次沒有延長資料窗、重新抓取歷史或啟動 Apify Actor，僅 GET 先前保存的兩個 dataset，以暫時恢復附件網址。私有網址未進 Git、日誌、快取或產物，runner 已清理暫存。

|項目|結果|
|---|---|
|本次走訪|102 個去重組|
|生成 HTTP 請求|101 次：100 次 HTTP 200、1 次 HTTP 429|
|通過固定格式|99 篇：38 訊號、46 無訊號、15 待確認|
|本次失敗|1 媒體前檢（0 生成）、1 標的格式（HTTP 200）、1 免費額度（HTTP 429）|
|最後有效回應／最新事件|2026-08-21 23:10:00 Asia/Taipei|
|額度停止所在貼文|2026-08-21 23:10:10 Asia/Taipei|
|下一筆尚未送出|2026-08-22 02:09:59 Asia/Taipei|
|剩餘|453 去重組，對應 456 來源貼文|
|完整 Pine|225 事件 = 原始 150 + 前次新增 37 + 本次新增 38|

走訪範圍包含待確認與失敗，不代表每篇均完成判讀。最新訊號日期不代替資料覆蓋或處理完成日期；原有測試與未解決項目均列入 inventory。跨平台同組可能有兩筆來源，因此本次走訪102組實際對應104篇，貼文狀態數與事件數不同。

全體來源貼文：有訊號 **77**、無訊號 **88**、待確認 **39**、技術失敗 **5**、媒體前檢失敗 **1**、狀態不明 **0**、尚未處理 **456**。失敗合計 **6**。

## 本次隔離項目

- [facebook:1619175659567023](https://www.facebook.com/DieWithoutBang/posts/pfbid0DfecTLy5chrHPu4SGwrQXpdrq3khfDSi6xeviUjy5xSBsHT7oLvfVSpSwYn3gFbYl) · 2026-08-06T17:52:45+08:00 · input_failure · HTTP None · attempts=0 · video_or_unknown_media_requires_review。保存於 data/history_progress/history-completion-20261107-005.json，沒有重送。
- [threads:3958223690278707712](https://www.threads.com/@banini31/post/Dbub3mImSIA) · 2026-08-07T12:30:55+08:00 · technical_failure · HTTP 200 · attempts=1 · invalid_ticker_format。保存於 data/history_progress/history-completion-20261107-005.json，沒有重送。
- [facebook:1632674428217146](https://www.facebook.com/reel/923659410206797/) · 2026-08-21T23:10:10+08:00 · technical_failure · HTTP 429 · attempts=1 · provider_http_error。保存於 data/history_progress/history-completion-20261107-009.json，沒有重送。

## 用量、服務回報及驗證

服務回報 gpt-5-mini／minimal，請求固定相同模型、推理設定與嚴格 schema；未獨立驗證底層模型或實際推理強度。原作者判讀政策及 hash 仍為 fork-7b626f2-ai-v1／8ccd8bbe6388705261e7240897417683f2dc6e2016f5db9d5eca462533837162。

本次已回報輸入 **277,179**、輸出 **14,659**、合計 **291,838 tokens**，reasoning tokens 回報0。無效標的格式的 HTTP200 用量仍計入；429未回傳usage，不宣稱其零tokens。點數扣除、剩餘點數與確切重設時刻未知；服務僅宣告免費請求已耗盡。模型查詢0、其他AI供應商查詢0；Apify dataset讀取2、Actor啟動0，沒有新增Actor費用回報或完整帳單資訊。

control 內保留前次阻塞歷史及本次基準：scope 從81次生成／187事件接續至182次生成／225事件；本次101次與累計182次不可重複相加。最新 summary.current_session 為本次獨立用量，summary其他scope用量為11/7起的累計。

142項既有離線測試、原有Pine重建一致性、225事件陣列配對／排序／方向／強度、原始150事件保留及政策hash檢查通過。接續時發現先前績效修正只套用到其中一條產生路徑而造成CI比對失敗，已讓原有social產生器沿用相同apply_accounting，未改判讀或績效標準。

225事件維持每段最多20事件、12個初始化函式；此新版未在TradingView實際編譯。用 candidates/8zz-history-latest.pine 全文取代 Pine Editor，儲存並更新圖表；GitHub不會自動同步。保留原作者署名及MPL-2.0。

既有績效頁、ZIP及市場快取維持前次187事件樣本快照，本次沒有額外抓行情、重算該頁或發布Pages；不要將該快照誤認為最新225事件的完整績效。

額度恢復後可從第一筆 not_started 接續；保留相同資料cutoff與已保存dataset，將本次阻塞加入blocker_history並更新本次基準，再由明確授權的一次性入口執行。完成、待確認、失敗與unknown不自動重送。本次入口已關閉，沒有定時喚醒或背景重試。

[雲端執行紀錄](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42456973950) · [全體清單](../data/history_completion_inventory.json) · [主報告](HISTORY_COMPLETION.md)
