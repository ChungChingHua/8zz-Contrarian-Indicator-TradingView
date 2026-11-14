# ChatAnywhere 403 排查（有限授權）

只排查現有故障，不新增產品功能。一般 pause 保持 true，兩個既有線上 workflow 與 Pages 維持停用。

靜態核對：base 為 https://api.chatanywhere.org/v1，GET 路徑 /models 組成 /v1/models，沒有重複或遺漏 /v1；Authorization 僅 Bearer + CHATANYWHERE_API_KEY，一次性 job 不注入官方 OpenAI 金鑰。執行時只記錄 Secret 是否存在、是否有換行／前後空白／重複 Bearer 前綴，不記錄值或前綴片段。格式不符即停止，不擅自改寫 Secret。

官方[模型清單文件](https://chatanywhere.apifox.cn/api-92222074)列 GET https://api.chatanywhere.tech/v1/models 與 Bearer Header；[README](https://github.com/chatanywhere/GPT_API_free)另確認 .org 與 .tech 均為接入點，免費版支援 GPT-5 系列且限制推理能力。沒有找到免費版明確不得查模型清單的官方說明。[FAQ](https://chatanywhere.apifox.cn/doc-2664690)稱 403 一般是餘額不足，但不能用這句概括此帳號與所有中介層錯誤。生成不可用不能由一次 models 403 推定。

本次上限：3 次無生成診斷、2 次條件式生成，無自動重試。診斷為 .org/models 帶金鑰、同路徑不帶金鑰作對照、以及文件列明 .tech/models 帶金鑰的接入點對照；若先取得有效清單即不繼續診斷。任何明確網路政策拒絕或安全 challenge 即停止，不繞過。只會對這兩個確認的 HTTPS 網域送金鑰，不跟隨 redirect，不關 TLS，不改代理或網路路由。

只有成功取得模型清單且列出 gpt-5-mini 才可使用已授權的固定 Facebook／Threads 樣本生成；快取清單不重查，不略過圖片、low 或 strict schema，不換模型。若仍不明，停止於診斷，不憑猜測跳過前檢查。

每次記錄狀態、Content-Type、安全化錯誤 type/code/message 與必要代理／服務相關標頭；移除金鑰、Bearer、URL、JWT、data URI，不儲存原始回應。標頭與錯誤格式只能作為歸因證據，不能獨立證明回覆身分。免費點數與帳號餘額若無欄位則記未知，不換算成 tokens。

診斷結果另存 data/social_chatanywhere_403_diagnostic_20261107.json；完成後停用本輪入口。沒有授權批次、排程、Pages 或合併。

## 本次實測結果與修正（授權已消耗，已停止）

[Actions 執行紀錄](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42348323173)。

| 請求 | 認證 | 狀態／回應證據 |
|---|---|---|
| GET https://api.chatanywhere.org/v1/models | CHATANYWHERE_API_KEY | 403；application/json；Server: cloudflare；頂層 error_code=1010、error_name=browser_signature_banned；detail 表示網站依客戶端瀏覽器簽章封鎖 |
| 同一路徑 GET 對照 | 不帶金鑰 | 同為 403／1010；顯示這個拒絕不依賴此次 Authorization 是否存在 |
| GET https://api.chatanywhere.tech/v1/models | 同一個 CHATANYWHERE_API_KEY | 200；application/json；Server: TencentEdgeOne；列出 gpt-5-mini |
| POST https://api.chatanywhere.tech/v1/responses | 同一個 CHATANYWHERE_API_KEY | 第一筆生成 200；格式有效，但要求 low、服務回傳 minimal，驗證拒絕並停止 |

Secret 實際注入成功，沒有換行、前後空白或重複 Bearer；/v1 路徑核對正確。同一金鑰在 .tech 列模型與生成都得到 200，因此不能將先前 .org 的 403 歸因為免費金鑰一律不能列模型或生成。回應是 Cloudflare 瀏覽器簽章拒絕的證據，和[Cloudflare 1010 官方說明](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)一致；不能僅由標頭獨立驗證整條供應商後端。

診斷器原先只辨識巢狀 error 與少數網路政策／challenge 標記，漏掉頂層 1010，因此仍完成另一個文件列明的接入點對照及一筆生成。這個停止判斷缺口已修正：未來遇到 1010／1020 或 browser_signature_banned，直接停止，不再做下一個接入點對照。本次未修改 User-Agent、TLS 驗證、代理、IP 或安全設定，也未再次測試。一般 ChatAnywhere 預設 base 已修正為本次取得成功回應的官方 .tech；一般線上暫停旗標仍為 true。

第一筆固定 Facebook 原文是「市場跟我說，孩子，你不用停損，因為你停不掉」。JPEG 實讀 34,147 bytes，SHA-256 b019bdb27af1913d7e35530f2125afad34b530fa093cee97ff53420940f71fcc，確實作為 input_image 附於生成請求。服務聲稱 images_reviewed=true，不能把此聲明或下載成功當作獨立驗證圖片理解。回傳候選：direction=0、strength=1、target=亞翔、ticker=6139；理由為自嘲／無奈、情緒模糊、clear=false，故不發訊號。這是**未採用的服務候選輸出**：雖本地固定格式檢查通過、服務回傳 strict=true，仍因 low 被回傳成 minimal 而保持 retry，不標為完成。

第二筆 Threads「展示新 GShock，表示下週穩了」沒有送出，未下載／附圖，沒有判讀、模型或用量結果。沒有為用滿兩次而繼續請求，也沒有把 low 改成 minimal。

服務回傳／宣稱模型 gpt-5-mini、reasoning.effort=minimal、input_tokens=803、output_tokens=256、total_tokens=1059、reasoning_tokens=0；不能獨立證明底層模型／思考過程。前後點數與剩餘請求額度未回傳，實際扣點未知，不宣稱零扣點，不將點數當 tokens。

HTTP 次數：無生成診斷 3（皆為 models GET）；生成 1；其他供應商查詢 0；圖片下載 1。GitHub 保存 audit 另有 contents GET／PUT 各一次；不包含 Actions 自身 checkout／日誌／產物服務流量。沒有自動重試、沒有官方 OpenAI 金鑰、沒有改模型、沒有批次／排程／Pages／合併。

原診斷器也把成功 JSON 的前綴誤放到錯誤摘要，包含不必要的加密回應欄位片段。最新審查檔已移除該成功回應前綴；修正後成功回應僅保留模型／格式／用量等必要欄位，不再保留原始成功內容。這不是金鑰，但不應作為錯誤訊息發布。既有執行產物／舊 commit 不會因最新檔修正而自動回收。

59 項離線測試與 Python 編譯通過，包括頂層 Cloudflare 1010 必須停止、成功回應不存為錯誤、診斷上限與敏感資訊遮蔽。實際 audit：data/social_chatanywhere_403_diagnostic_20261107.json。一次性入口再次停用，所有請求已停止。
