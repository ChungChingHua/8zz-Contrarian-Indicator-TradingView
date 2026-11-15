> **目前執行版本：** 原作者規則的單批5次已完成並停止，.tech/v1與gpt-5-mini／minimal保留。手動worker、遠端帳本與本批結果見[還原協定](ORIGINAL_AUTHOR_RESTORATION.md)、[本批結果](HISTORY_BATCH_01_RESULTS.md)。下方先前兩筆smoke／品質測試限制是歷史紀錄，不是新批次授權。

> **線上功能暫停，請勿設定後直接執行 smoke。** 本次資安審查不授權模型查詢、貼文／圖片傳送、排程或合併。見[資安審查](SECURITY_REVIEW.md)。

# ChatAnywhere 免費版小量驗證（目前設定）

此設定取代 AUTOMATION.md 中先前以 OpenAI 官方作為必要供應商的說明。原始資料、過濾、去重、恢復、績效及 Pine 生成保留。

- GitHub Actions 只注入獨立 `CHATANYWHERE_API_KEY`，必須從 ChatAnywhere 免費帳號取得；不注入 `OPENAI_API_KEY`，程式也不會以它代替第三方金鑰。
- `AI_PROVIDER=chatanywhere`，固定服務網址 `https://api.chatanywhere.org/v1`；官方供應商設定仍獨立保留，沒有自動切換或任意 base URL。帶憑證請求拒絕 HTTP redirect。
- 優先且僅測 `gpt-5-mini`，推理強度 `low`。不自動測試或選用其他型號、付費模型。其他 GPT-5 型號僅從帳號 `/v1/models` 列表回報；列出不代表免費或可用於全部功能。
- 缺少 Secret 時不進行第三方呼叫。先用 GET /v1/models 做帳號查詢；未列出 gpt-5-mini 即停止，不做生成。
- 通過前檢查後僅兩個既有樣本 smoke：必須實際圖片 bytes＋原文一起送入 POST /v1/responses，使用 text.format json_schema strict=true 與 reasoning.effort=low。不轉 Chat Completions、不移除圖片／Schema／推理欄位。
- 回應必須回報 gpt-5-mini 系列、strict schema 設定及相同 reasoning effort；未回報就標示相容性未確認、留 retry，不當成功。參數接受及回傳不能獨立證明服務後端真正採用相同推理強度或模型權重。
- 402／429 立即保存進度並停止，不繼續另一篇，不切換供應商或模型。其他介面不相容也如實記錄，不透過降級重試。既有成功結果按供應商與模型隔離。
- 免費剩餘點數：官方文件僅確認查詢網站，尚未確認可程式使用的帳號剩餘點數 API。因此僅記錄實際回傳的 rate-limit 剩餘欄位，沒有回傳時明示 unknown，不能將 tokens 換算為免費剩餘點數，或將官方公開總配額當作此帳號餘額。請到 https://api.chatanywhere.org 的帳號查詢頁核對。
- `data/social_chatanywhere_preflight.json` 保存模型清單／前檢查；`social_smoke_results.json` 保存判讀／圖片證據；validation 保持 false，直到完整驗證通過。供應商公開免費 GPT-5 支援不等於已驗證此帳號所有相容性。

設定步驟：GitHub 本儲存庫 → Settings → Secrets and variables → Actions → New repository secret → `CHATANYWHERE_API_KEY`，填入 ChatAnywhere **免費版**金鑰。不必修改／提供官方 OpenAI 金鑰。設定後在 PR 分支手動 Run workflow、mode=smoke。此次授權只涵蓋兩筆；workflow 只提供 smoke，程式也拒絕 ChatAnywhere batch。排程保持移除、PR 不合併。

已核對服務來源：

- [官方免費服務 README](https://github.com/chatanywhere/GPT_API_free)：免費 GPT-5 系列、免費推理強度受限制；配額會變動，不能拿舊搜尋摘要當帳號餘額。
- [官方 Responses API 文件](https://chatanywhere.apifox.cn/api-385209336)
- [官方操作文件與查詢網站](https://docs.chatanywhere.tech/)

目前離線測試 37 項通過；帳號模型、免費剩餘額度與四項功能的實測結果以本次 Actions 紀錄為準，不由文件支援宣稱推定。

## 本次 Actions 結果

[PR 分支執行紀錄](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42256948503)確認 CHATANYWHERE_API_KEY 在 Actions 是空值。流程已在任何供應商呼叫前停止：模型清單查詢 0 次、生成 0 次、沒有動用官方金鑰。因此實際可用的 GPT-5 型號、剩餘額度與 Responses／圖片／嚴格 Schema／推理強度四項相容性均尚未實測；不能因文件有列出接口就宣稱帳號可用。

最終離線測試 37 項通過，包含未提供第三方金鑰不可替用官方金鑰、模型未列出不生成、不選付費型號、額度錯誤立即保留進度並停止、認證轉址拒絕與相容性缺欄失敗。推送驗證觸發器已移除，未啟用 schedule、未批次或合併。
