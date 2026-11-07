# ChatAnywhere minimal 有限技術驗證（2026-11-07，已停止）

同一 PR #1，保留 `https://api.chatanywhere.tech/v1`。本輪只新增一個 Threads 生成請求，無重試、無模型／額度查詢。Facebook 使用已保存回應，不重送。659 篇 archive 與 Pine 未修改；一般 pause、排程與 Pages 保持停用，未合併 PR。一次性 workflow 已改為無 Secret 的停用 stub，runner 亦以 scope、既有 consumed 報告、分支與 run_attempt=1 防止重跑。

## 請求設定與服務回報

| 樣本 | 實際請求設定 | 服務回報／宣稱 | 驗證範圍 |
| --- | --- | --- | --- |
| Facebook（既有） | gpt-5-mini；low；strict JSON schema；1 張圖片 | gpt-5-mini；minimal；json_schema / strict=true；images_reviewed=true | 已保存 JSON 欄位重新通過現行分類驗證；使用者本次接受 minimal 作技術評估，並未追溯改寫原請求 low |
| Threads（本次） | gpt-5-mini；minimal；strict JSON schema；1 張圖片；store=false；無工具 | gpt-5-mini；minimal；json_schema / strict=true；images_reviewed=true | HTTP 200；實際輸出鍵、型別、列舉、長度、標的格式及必要圖片旗標驗證通過 |

這些模型、推理強度及 reasoning token 數字均為服務回傳，未獨立驗證底層模型或實際推理行為。`passed=true` 只表示本次 Threads 的傳輸與必要格式檢查通過，不能視為分類品質或 659 篇批次授權。

Facebook 完整原始 API 回應未保存，只有完整分類 JSON、用量、設定摘要與媒體證據。因此離線重驗以已存欄位重建驗證輸入，不能重驗完整原始封包、原始完成狀態／所有 output item，也未重新看圖或證明供應商確實做了視覺推論。舊 audit 仍保留原先 low/minimal 不一致而停止的原因；新 audit 的 review 是本次重新評估結果，沒有把原失敗改成歷史成功。

## 逐筆結果與人工複核

### Facebook：不用停損，因為停不掉

- [來源](https://www.facebook.com/DieWithoutBang/posts/pfbid03143n7ECXc3swjAwzFvjXJFrfksuaecAmRtRR5uV5yaYAvtNQVrh2WDpG1ciUKMXsl)，作者時間 2026-11-06 09:15:20 Asia/Taipei；post ID 1703774981107090。
- 原文：「市場跟我說／孩子，你不用停損…／因為你停不掉」。服務結果：investment_related=true、clear=false、direction=0、strength=1、target=亞翔、ticker=6139，status=review。
- 服務理由為自嘲、無奈，單篇無法形成明確情緒結論。人工複核維持**不確定、不產生訊號**：不知道具體部位、不能停損的原因或情緒強度，不能僅見「停損」就判成恐慌反向買點。情緒訊號本來不要求明確買賣宣告，這裡的不足是情緒與上下文證據不足。
- 既有紀錄證實 JPEG 34,147 bytes 已下載並以 data URI 附於該次請求，SHA-256 `b019bdb27af1913d7e35530f2125afad34b530fa093cee97ff53420940f71fcc`；模型回傳 images_reviewed=true。下載及附圖不等於證明模型看懂圖片。
- 亞翔／6139 不在原文。保存的理由沒有指出圖中哪個可見資訊支持它，本輪亦未重新取圖獨立核對，**不能確認圖片增加有效投資證據，該標的待確認**。
- `quoted_summary` 把作者的「市場跟我說」修辭當成引用摘要；不能據此認定存在第三方引用文章。保留服務原結果，記錄為語意品質缺點。

### Threads：GShock，下週穩了

- [來源](https://www.threads.com/t/DfZyOhEGS6y)，作者時間 2026-11-06 22:07:49 Asia/Taipei；post ID 4024468641932717746。
- 原文：「沒事，就是給大家看看我的新GShock／然後跟大家說，看來下週穩了」。服務結果：investment_related=true、clear=false、direction=0、strength=1、target/ticker 空白，status=review。
- 服務理由明說：文字配合展示手錶，未指明投資標的；圖片是 G-Shock 手錶近照，沒有股票或交易介面。這是**服務對圖片的描述**，不是獨立人工看圖驗證。
- JPEG 628,272 bytes 下載成功，SHA-256 `d05341342435ce668ab641a4ac7a0ec0cb3172bd5e234891b294b5c5eed24415`；實際生成 payload 含 1 個 input_image data URI；回應 images_reviewed=true 並描述圖片內容。未把簽名圖片 URL 送入模型或發布於新產物。
- 根據取得的文字與服務所述圖片，**沒有足夠投資證據；不產生訊號**。圖片描述支持生活情境，沒有增加投資訊號的有效證據。
- 語意缺點：investment_related=true 缺乏理由支持，且 quoted_summary 只是複述本人原文，不能當成第三方引用；人工評估為投資關聯不足。保留原始候選欄位，不偷偷改寫模型答案。技術成功不等於語意完全合格，後續批次前仍須處理／確認這些品質問題。

## 用量與請求次數

| 樣本 | input tokens | output tokens | total tokens | reasoning tokens（服務回報） | 本輪新增生成 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Facebook，既有回應 | 803 | 256 | 1,059 | 0 | 0 |
| Threads，本輪 | 1,371 | 296 | 1,667 | 0 | 1 |

本輪 HTTP：模型查詢 **0**、生成 **1**、其他供應商查詢 **0**、圖片下載 **1**；無自動重試。兩筆原定樣本合計歷次成功生成用量 2,726 tokens，**本輪新增只有 1,667 tokens**。點數不等於 tokens。

前後免費點數、實際扣點與剩餘請求額度皆無可取得欄位（remaining headers 為空，quota_before/after=null），亦未額外查詢帳號。**實際扣點未知，不能宣稱零扣點**。未估算金額或將 token 換算免費點數。

Actions checkout、log／artifact 及 GitHub 控制平面不計入供應商請求數；專用 audit 保存另有 GitHub contents GET 1 次與 PUT 1 次。

## 證據與測試

- [本輪 Actions（成功）](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42349313551)
- [本輪保存 audit](../data/social_chatanywhere_minimal_20261107.json)
- [Facebook 既有 audit 與 403 排查](../data/social_chatanywhere_403_diagnostic_20261107.json)
- [原有 403 排查說明](CHATANYWHERE_403_DIAGNOSIS.md)
- 62 項離線測試通過，涵蓋舊功能、保存 Facebook 不發送、minimal 單次 Threads 上限、禁止 models／官方備援路徑、失敗留 retry、429 不重試與一般 pause 保留；Actions 執行相同測試通過。

未使用 OPENAI_API_KEY 或其他 AI 憑證。用途仍限技術評估；免費版是否允許個人交易研究未確認，更不推定客戶或商業服務可用。沒有批次、啟用排程、發布 Pages 或合併 PR；完成即停止。
