# 2026/11/9 額度恢復後續跑結果

本次按遠端帳本持續執行，直到 ChatAnywhere 回傳 HTTP429，明確表示共用24小時100次免費請求額度已耗盡而保存停止。**歷史判讀尚未補齊**；沒有自動重試、更換模型／供應商／付費服務或使用官方OpenAI金鑰備援。

資料窗仍截至 **2026-11-07T20:15:59.578797+08:00**，封存666篇，沒有延伸至11/9。Actor啟動0，僅讀取原有dataset 2次恢復暫存媒體網址；未重抓歷史、未提高Apify費用上限或儲值。私有網址未進Git／日誌／快取／產物，runner已清理暫存。

|項目|結果|
|---|---|
|本次走訪|101去重組，對應102筆來源貼文|
|生成HTTP|101次，100次HTTP200、1次HTTP429|
|通過固定格式與一致性驗證|97篇|
|本次結果|訊號31、無訊號53、待確認15、技術失敗2|
|待確認細分|2篇輸出矛盾，其餘資訊不足；矛盾原回應保留，不改猜方向，不產生箭頭|
|最後有效判讀|2026-09-04T11:02:25+08:00|
|最新訊號|2026-09-03T13:38:49+08:00|
|額度停止貼文|2026-09-04T16:11:55+08:00|
|下一筆未送出|2026-09-04T18:25:40+08:00|
|尚未處理|352去重組／354來源貼文|
|完整Pine|256事件 = 原歷史150 + 前次新增75 + 本次新增31|

以上發文時間均為Asia/Taipei。走訪範圍包含待確認／失敗，不代表每篇判讀完成；最新訊號日期不能代替資料覆蓋或處理完成日期。

全體來源貼文：有訊號108、無訊號142、待確認54、技術失敗7、媒體前檢失敗1、狀態不明0、尚未處理354。失敗合計8。既有測試、待確認及失敗全部仍列在inventory，沒有視為完成或重送。跨平台同組會對應多筆來源，但只產生一個事件。

## 本次需確認／失敗項目

- [facebook:1634810338003555](https://www.facebook.com/DieWithoutBang/posts/pfbid0TZQEndQH8J1odG1fuTHZEjTCUab5qZxENrgNxKhEyykyzEyDnNd182w6EqicQ4ZAl) · 2026-08-24T08:57:22+08:00 · technical_failure · HTTP 200 · invalid_ticker_format；保存於 data/history_progress/history-completion-20261107-010.json，未重送。
- [threads:3971208920530747764](https://www.threads.com/@banini31/post/DcckXkNGQF0) · 2026-08-25T10:30:15+08:00 · pending_confirmation · HTTP 200 · contradictory_output_fields；保存於 data/history_progress/history-completion-20261107-010.json，未重送。
- [facebook:1638326184318637](https://www.facebook.com/DieWithoutBang/posts/pfbid02J74EFoyiMKqeee8KUHj4e1kh5DVSM9CMbfgDGNhfv2HtdU1Rx68jdqoxu9cBKAqtl) · 2026-08-28T10:15:46+08:00 · pending_confirmation · HTTP 200 · contradictory_output_fields；保存於 data/history_progress/history-completion-20261107-012.json，未重送。
- [facebook:1644567720361150](https://www.facebook.com/reel/919300347914420/) · 2026-09-04T16:11:55+08:00 · technical_failure · HTTP 429 · provider_http_error；保存於 data/history_progress/history-completion-20261107-014.json，未重送。

## 用量、驗證與接續

服務回報輸入 **297,527**、輸出 **16,495**、合計 **314,022 tokens**，reasoning tokens回報0。包含格式失敗與矛盾回應的用量；429未回傳usage，不假定零tokens。實際點數扣除、剩餘點數及精確重設時刻未知，服務僅宣告免費請求已耗盡。模型清單及其他AI查詢皆0。

請求固定免費CHATANYWHERE_API_KEY、.tech/v1、gpt-5-mini／minimal／strict schema；模型與推理僅為服務回報，未獨立驗證底層模型或實際推理強度。原作者政策、few-shot、排除、情緒／強度規則未改，hash仍為8ccd8bbe6388705261e7240897417683f2dc6e2016f5db9d5eca462533837162。沒有新增真實驗收樣本。

本次指標見summary.current_session；scope累計生成由182至283次，本次101次不可再與累計數相加。前次基準與阻塞保留於control的session_history／blocker_history，原回應與processed分別保存於history_progress。

142項既有離線測試、Pine重建一致性、256事件陣列配對／排序／方向強度及原始150事件保留檢查通過。初始化仍為每段最多20事件、13個函式，避免單一if過長；此最新版未在TradingView實際編譯。保留作者署名與MPL-2.0。

完整最新版：candidates/8zz-history-latest.pine；手動全文取代TradingView Pine Editor、儲存並更新圖表，GitHub不會自動同步。既有績效頁／ZIP／市場快取維持先前187事件樣本快照，本次未抓行情或重算該頁，勿視為256事件的完整績效。

額度恢復後從 2026-09-04T18:25:40+08:00 的第一篇not_started接續；保留同一資料cutoff與已保存dataset，先封存本次阻塞並更新基準，再使用明確授權的一次性入口。完成、待確認、失敗與unknown不自動重送。本次入口已停用，未啟用持續排程、發布Pages或合併PR。

[雲端執行紀錄](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42576742068) · [全體清單](../data/history_completion_inventory.json) · [主報告](HISTORY_COMPLETION.md)
