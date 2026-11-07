# ChatAnywhere 403 排查（有限授權）

只排查現有故障，不新增產品功能。一般 pause 保持 true，兩個既有線上 workflow 與 Pages 維持停用。

靜態核對：base 為 https://api.chatanywhere.org/v1，GET 路徑 /models 組成 /v1/models，沒有重複或遺漏 /v1；Authorization 僅 Bearer + CHATANYWHERE_API_KEY，一次性 job 不注入官方 OpenAI 金鑰。執行時只記錄 Secret 是否存在、是否有換行／前後空白／重複 Bearer 前綴，不記錄值或前綴片段。格式不符即停止，不擅自改寫 Secret。

官方[模型清單文件](https://chatanywhere.apifox.cn/api-92222074)列 GET https://api.chatanywhere.tech/v1/models 與 Bearer Header；[README](https://github.com/chatanywhere/GPT_API_free)另確認 .org 與 .tech 均為接入點，免費版支援 GPT-5 系列且限制推理能力。沒有找到免費版明確不得查模型清單的官方說明。[FAQ](https://chatanywhere.apifox.cn/doc-2664690)稱 403 一般是餘額不足，但不能用這句概括此帳號與所有中介層錯誤。生成不可用不能由一次 models 403 推定。

本次上限：3 次無生成診斷、2 次條件式生成，無自動重試。診斷為 .org/models 帶金鑰、同路徑不帶金鑰作對照、以及文件列明 .tech/models 帶金鑰的接入點對照；若先取得有效清單即不繼續診斷。任何明確網路政策拒絕或安全 challenge 即停止，不繞過。只會對這兩個確認的 HTTPS 網域送金鑰，不跟隨 redirect，不關 TLS，不改代理或網路路由。

只有成功取得模型清單且列出 gpt-5-mini 才可使用已授權的固定 Facebook／Threads 樣本生成；快取清單不重查，不略過圖片、low 或 strict schema，不換模型。若仍不明，停止於診斷，不憑猜測跳過前檢查。

每次記錄狀態、Content-Type、安全化錯誤 type/code/message 與必要代理／服務相關標頭；移除金鑰、Bearer、URL、JWT、data URI，不儲存原始回應。標頭與錯誤格式只能作為歸因證據，不能獨立證明回覆身分。免費點數與帳號餘額若無欄位則記未知，不換算成 tokens。

診斷結果另存 data/social_chatanywhere_403_diagnostic_20261107.json；完成後停用本輪入口。沒有授權批次、排程、Pages 或合併。
