# 本次驗證紀錄

- 儲存庫：ChungChingHua/8zz-Contrarian-Indicator-TradingView；已確認 push/admin 權限，工作分支 codex/social-pipeline-20261106，PR #1。
- 上傳檔案：Facebook 285 → 284，排除其他作者 1；Threads 399 → 375，排除回覆 24。原檔 SHA-256 與筆數見 data/import_manifest.json。
- 22 項離線測試及 Python 編譯檢查通過。包含嚴格布林辨識欄位、作者、引用、重跑與內容修改、方向不同不合併、圖片失敗不發訊號、雙方向虧損、勝率分母、分頁游標、啟動結果不明不重複付費、已知 HTTP 拒絕可在修正後重試、恢復既有 run。
- 完整 Pine 重建前後 SHA-256 相同；歷史事件區塊保留。Python 能產生 .pine 不代表 TradingView 已編譯通過。
- [GitHub 離線 CI](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42249312652)通過。
- [小量雲端驗證](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42249298052)：Facebook 實抓 2、接受 2；Threads 前一次實抓 2、接受 2，本次重用 24 小時內成功結果避免重付費。Facebook 原先 HTTP 400 已修正：官方 Schema 接受 UTC Z 格式，拒絕 +00:00 日期字串。最終兩個來源均成功。
- `APIFY_TOKEN` 實際驗證可用。`GOOGLE_API_KEY` 在 Actions 是空值，因此未執行任何 AI 請求；整體 smoke **未通過**，validation.passed=false，持續付費排程尚未啟用。未讀取或揭露任何金鑰內容。
- 659 篇均仍待 AI／圖片判讀，新增社群訊號 0；不能宣稱已補齊 2026-07-20 至今的有效交易訊號。資料匯入已完成，語意判讀被缺少 AI 憑證阻塞。
- 舊行情快取重建：Mode B 41 勝／21 敗、Mode A 45 勝／24 敗。只驗證統計修正，不是即時行情績效。
- 未驗證：Gemini 模型與帳戶額度的實際呼叫、全部歷史圖片可讀性與判讀品質、最新行情、TradingView 編譯／提醒、GitHub Pages 部署、合併後排程。排程亦可能受 GitHub 的 fork／閒置政策影響，需在 Actions 確認啟用。

下一步：設定 GOOGLE_API_KEY → 在此分支手動跑 smoke → 成功後按預算分批 classify-only → 檢查產生的訊號與完整 Pine → 合併 PR → 手動更新 TradingView。若本月需要完成全部 659 篇，MONTHLY_AI_LIMIT 可暫設 1000；每次 AI 仍最多 50 篇。
