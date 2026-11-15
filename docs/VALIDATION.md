# 本次驗證紀錄

- 儲存庫：ChungChingHua/8zz-Contrarian-Indicator-TradingView；已確認 push/admin 權限，工作分支 codex/social-pipeline-20261106，PR #1。
- 上傳檔案：Facebook 285 → 284，排除其他作者 1；Threads 399 → 375，排除回覆 24。原檔 SHA-256 與筆數見 data/import_manifest.json。
- 22 項離線測試及 Python 編譯檢查通過。包含嚴格布林辨識欄位、作者、引用、重跑與內容修改、方向不同不合併、圖片失敗不發訊號、雙方向虧損、勝率分母、分頁游標、啟動結果不明不重複付費、已知 HTTP 拒絕可在修正後重試、恢復既有 run。
- 完整 Pine 重建前後 SHA-256 相同；歷史事件區塊保留。Python 能產生 .pine 不代表 TradingView 已編譯通過。
- [GitHub 離線 CI](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42249312652)通過。
- [小量雲端驗證](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42249298052)：Facebook 實抓 2、接受 2；Threads 前一次實抓 2、接受 2，本次重用 24 小時內成功結果避免重付費。Facebook 原先 HTTP 400 已修正：官方 Schema 接受 UTC Z 格式，拒絕 +00:00 日期字串。最終兩個來源均成功。
- `APIFY_TOKEN` 實際驗證可用。`OPENAI_API_KEY` 在 Actions 是空值，因此未執行任何 AI 請求；整體 smoke **未通過**，validation.passed=false，持續付費排程尚未啟用。未讀取或揭露任何金鑰內容。
- 659 篇均仍待 AI／圖片判讀，新增社群訊號 0；不能宣稱已補齊 2026-07-20 至今的有效交易訊號。資料匯入已完成，語意判讀被缺少 AI 憑證阻塞。
- 舊行情快取重建：Mode B 41 勝／21 敗、Mode A 45 勝／24 敗。只驗證統計修正，不是即時行情績效。
- 未驗證：OpenAI 模型與帳戶額度的實際呼叫、全部歷史圖片可讀性與判讀品質、最新行情、TradingView 編譯／提醒、GitHub Pages 部署、合併後排程。排程亦可能受 GitHub 的 fork／閒置政策影響，需在 Actions 確認啟用。

下一步：設定 OPENAI_API_KEY → 在此分支手動跑 smoke → 成功後按預算分批 classify-only → 檢查產生的訊號與完整 Pine → 合併 PR → 手動更新 TradingView。若本月需要完成全部 659 篇，MONTHLY_AI_LIMIT 可暫設 1000；每次 AI 仍最多 50 篇。

## OpenAI 遷移驗證（取代上方 AI 設定與排程說明）

已確認舊程式使用 Google generateContent，現已實際改成 OpenAI Responses API。上方小量抓取紀錄只證明 Apify 成功，不代表 OpenAI 已驗證。此次僅執行離線 mock 測試，未呼叫任何付費 API，未處理 659 篇。OPENAI_API_KEY 是否已設定尚未透過付費工作驗證；不要沿用先前 Google Secret 缺少的紀錄來推論此 Secret 的狀態。排程觸發器已移除，validation 重設 false；PR #1 保持未合併。設定與小量費用驗證步驟見 AUTOMATION.md。

本次遷移：27 項離線測試、Python 編譯檢查通過；全程無付費 API 呼叫。

## 已設定 OpenAI Secret 後的線上 smoke（未通過）

GitHub Actions 在 PR 分支成功取得 Secret；此次沒有重抓 Apify、沒有批次判讀、沒有啟用排程或合併。原先 Facebook 最新圖片的 CDN 網路不可達，因此以既有匯入資料中較早、經免費下載前檢查可讀的 Facebook 貼文替代；Threads 的 photo 類型相容性已修正。

最終兩筆：

- Facebook `1703774981107090`：原文「市場跟我說，孩子，你不用停損，因為你停不掉」。JPEG 實讀 34,147 bytes，SHA-256 見 data/social_smoke_audit.json。
- Threads `4024468641932717746`：原文展示新 GShock，表示「看來下週穩了」。JPEG 實讀 628,272 bytes，SHA-256 見同檔。

兩筆均將實際圖片 bytes 作為 input_image，連同原文送出 Responses API。指定模型 gpt-4.1-mini，但兩筆都得到 HTTP 429；供應商未提供可辨識的錯誤代碼，因此不能確定是短期限流或專案額度不足。沒有回傳模型實際版本、方向、強度、標的、理由或 token usage，結構化輸出與判讀合理性仍未完成線上驗證。不可將這兩篇視為判讀成功。

含修正後重試，總計 5 次 Responses HTTP 請求，成功 0 次；前兩次工作流程在圖片前檢查失敗，沒有送出 AI 請求。兩個樣本留 retry，原先無法讀圖的貼文也留 retry，沒有新增訊號。停止線上重試，等待確認 OpenAI 專案的 rate limits／usage／額度狀態；不用提供金鑰明文。

沒有 usage 或帳單資料，故實際與估算費用均標示 unavailable，不把失敗請求宣稱為免費或零 token。計費仍須核對 OpenAI 專案帳單。最終線上 run： https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42253893332 。

29 項離線測試通過，包括 HTTP 429 狀態保留及錯誤代碼白名單，原始 provider 錯誤與憑證不輸出。驗證用 push 觸發器再次移除，保留手動操作；PR 不合併、排程不啟用。

自動審核曾拒絕把帶簽名的備援 CDN 網址新增到公開 Git，因可能授予媒體存取權。該檔案沒有提交；最終改用已存在資料中的另一篇可讀圖片樣本。
