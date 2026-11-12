# 2026/11/12 歷史續跑與憑證阻塞

沿用原作者規則，未修改判斷標準。尚未補齊。

- 抓取截止：台灣時間 2026/11/7 20:15:59，共666篇。
- 本輪生成8次，8次HTTP 200且格式通過：3有訊號、4無訊號、1待確認；無新技術失敗或狀態不明。
- 已走訪至2026/10/19 11:29:06，下一篇2026/10/19 21:45:39。較早待確認／失敗未當成完成。
- 最新事件2026/10/15 09:15:46；完整候選Pine344事件（原歷史151、累計新增193，本輪新增3）。
- 全部來源貼文：有訊號195、無訊號241、待確認78、技術失敗9、媒體輸入失敗4、狀態不明0、尚未處理139；去重後剩139組。
- 服務回傳tokens：輸入23058、輸出1529、合計24587，reasoning_tokens 0。請求設定保持ChatAnywhere .tech/v1、gpt-5-mini、minimal；不宣稱獨立驗證模型或實際推理。
- 實際扣點與剩餘免費點數／請求額度未取得，不能由tokens推算扣點或宣稱零扣點。

## 阻塞證據

更新下一批公開圖片前，Apify官方Actor metadata查詢遭拒。另一次無生成唯讀診斷確認Secret已注入且非空，但HTTP **401**、Content-Type **application/json**、錯誤代碼 **user-or-token-not-found**，固定標記「token is not valid」。究竟是撤銷、值錯誤或其他帳號問題無法確認。不是本輪已確認的AI額度耗盡。

[診斷帳本](../data/history_media_repairs/preflight-diagnostic-20261112.json)／[續跑執行](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/43190962491)／[診斷執行](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/43192118447)。

Apify metadata GET1次、另一次診斷GET1次，POST0、新Actor啟動0；月計數57/70。沒有本輪新run費用可結算，不代表AI或其他服務免費。未反覆重試認證。

## 接續方式

1. 在Apify Console取得有效API token。
2. GitHub儲存庫 Settings → Secrets and variables → Actions，更新 **APIFY_TOKEN**，只填token本體，不加Bearer、引號或換行；不要貼在聊天或日誌。
3. 保留CHATANYWHERE_API_KEY。從遠端帳本下一篇接續，已完成、待確認、失敗與狀態不明不自動重送。
4. 最新快取：run **43190962491**，**history-media-cache-20261112-continuation**，artifact **13931291105**，7269912 bytes，到期 **2026-11-26T09:24:39Z**。恢復後仍須驗證hash、MIME、magic與路徑；只清理工作副本，來源artifact保留。到期後需重新評估媒體取得。

原始回應、來源、規則版本與結果保留。完整Pine已重建，未經TradingView實際編譯。九月底策略及既有ATR／移動停損改動保留。

快取離線測試9項通過，含401不重試、不啟動Actor。完整回歸以GitHub Actions完整checkout為準；本機部分鏡像缺檔，不能作完整回歸證據。

本次兩個一次性入口已停用。不啟用排程、不發布網站、不發Telegram、不合併PR。
