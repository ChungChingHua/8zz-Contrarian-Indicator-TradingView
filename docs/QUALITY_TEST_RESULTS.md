# 10篇盲測結果（測試紀錄，不是正式Pine訊號）

每筆只使用原貼文快照及實際附圖，**外部上下文一律無**。候選答案未進prompt；規則與輸入於執行前凍結，生成後才比對。候選不是標準答案，差異不等於模型錯誤；本輪不計算「準確率」。圖片觀察與轉錄均為服務輸出，**沒有人工核圖**。

[固定規則與限制](QUALITY_PROTOCOL.md)；完整原文與圖片連結見 [樣本](QUALITY_SAMPLES.md)。

## 請求與用量

實際HTTP：{"generation": 9, "model_queries": 0, "other_provider_queries": 0, "image_downloads": 6}。無自動重試。

API回報token加總：{"input_tokens": 13076, "output_tokens": 5288, "total_tokens": 18364, "reasoning_tokens": 0}。僅加總取得的usage；模型與推理資訊為服務回報／宣稱，未獨立驗證底層模型或推理。

前後免費點數、剩餘請求額度與實際扣點若無回傳則未知；點數不是tokens，不宣稱零扣點，不估算點數。實際quota欄位：{"quota_before": null, "quota_after": null, "actual_points_deducted": null}

請求設定：{"base": "https://api.chatanywhere.tech/v1", "model": "gpt-5-mini", "reasoning_effort": "minimal", "strict_schema": true, "store": false, "tools": false}

整輪已取得10篇答案：False；異常停止：False。未取得答案的樣本不標記完成。

| # | 原文摘要 | 相關性 | 情緒／方向／強度 | 圖片 | 狀態 |
| --- | --- | --- | --- | --- | --- |
| 1 | 連我的BTC單都沒了 這一波應該⋯ 狠恐怖 感覺比七月的還猛_(:_」∠)_  大家風控要做好， | investment | panic / 1 / 3 | 1/1附圖 | evaluated_test_only |
| 2 | 爽啦！ 喬喬賺錢了！ 加碼再賺！ 台股簡單啦 | investment | euphoria / -1 / 2 | 0/0附圖 | evaluated_test_only |
| 3 | 我還有  原本價值300萬的個股還沒停損 至於主動ETF.. 隨便他了_(:_」∠)_ | investment | panic / 1 / 2 | 0/0附圖 | evaluated_test_only |
| 4 | 沒事， 就是給大家看看我的新GShock 然後跟大家說， 看來下週穩了 | insufficient_information | insufficient_information / 0 / 1 | 1/1附圖 | evaluated_test_only |
| 5 | 買欣興，欣興會被警調 買康霈，康霈會⋯  但是投資自己，一定沒有錯！ 因為不管是男人/女人，都有 | 未取得 | 未取得 / — / — | 0/1附圖 | input_review |
| 6 | 今天穩了！ 大家一起跟我念！ 一天100點，台股5萬點！ | investment | euphoria / -1 / 2 | 1/1附圖 | evaluated_test_only |
| 7 | 今日我的庫存 我好痛苦_(:_」∠)_  為什麼我要貪心買個股⋯ 目前貸款買的部分都是大虧⋯⋯⋯ | investment | panic / 1 / 3 | 1/1附圖 | evaluated_test_only |
| 8 | 市場跟我說 孩子， 你不用停損... 因為你停不掉_(:_」∠)_ | investment | panic / 1 / 2 | 1/1附圖 | evaluated_test_only |
| 9 | 恐慌的睡不著 | insufficient_information | insufficient_information / 0 / 1 | 0/0附圖 | evaluated_test_only |
| 10 | 現在的我呈現一個 因為部分停損，所以大漲不爽 因為還沒損完，所以續跌痛苦 的狀態矛盾狀態_(:_ | investment | mixed / 0 / 2 | 1/1附圖 | evaluated_test_only |

## 1. facebook：facebook:1696581131826475

[來源](https://www.facebook.com/DieWithoutBang/posts/pfbid0euW28fo5eBPr4X7SsmhcDaoVxD1Un5iz7SkPvY23szM8j9mV73JoHmcVgzw8xs5el) · 2026-10-30T08:05:00+08:00（Asia/Taipei）

原文摘要：連我的BTC單都沒了 這一波應該⋯ 狠恐怖 感覺比七月的還猛_(:_」∠)_  大家風控要做好， 該停損停損啊

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件1張，實際附於生成請求1張；下載成功=True（無附件時為不適用），未人工核圖。
- 下載證據：{"sha256": "d9085f60d15ebcf0c33999f0dd03587b72838088c84e8d88f4b58b60d1be193f", "bytes": 28506, "mime": "image/jpeg"}

相關性：**investment**。理由：作者明確提到BTC單被止損與提醒大家風控停損，顯示討論加密貨幣交易情境。

情緒：**panic**；反向方向 **1**；強度 **3**。理由：作者表示自己的BTC單已沒了、稱此波「狠恐怖」並建議他人要做好風控與停損，語氣表達強烈的驚恐與挫折。

圖片觀察（服務聲稱）：{"image_index": 0, "readable": true, "observation": "截圖顯示TSM股票價格與當日走勢圖，包含數值與時間標示。", "visible_text": "TSM\n431.81 USD\n▼7.70 (1.75%)\n收盤價 | 2026/10/30 04:00 台北時間", "investment_information": true, "limitation": "圖片顯示TSM價格與走勢，但貼文文字並未提及TSM是否為作者持倉或與BTC單關聯。"}

標的候選及證據：{"name": "BTC", "ticker": "", "relationship": "author_stance", "evidence": [{"source": "author_text", "image_index": -1, "quote": "連我的BTC單都沒了", "sha256": null, "evidence_status": "literal_text_match", "human_verified": false}], "name_supported": true, "ticker_supported": false, "human_verified": false, "status": "text_supported"}

標的候選及證據：{"name": "TSM", "ticker": "TSM", "relationship": "mentioned_only", "evidence": [{"source": "image", "image_index": 0, "quote": "TSM\n431.81 USD\n▼7.70 (1.75%)\n收盤價 | 2026/10/30 04:00 台北時間", "sha256": "d9085f60d15ebcf0c33999f0dd03587b72838088c84e8d88f4b58b60d1be193f", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": true, "ticker_supported": true, "human_verified": false, "status": "pending_human_confirmation"}

本人評論：作者表達對其比特幣交易遭遇強烈負面情緒並提醒他人停損；附圖為TSM價格截圖，但無文字說明兩者關聯。

第三方引用摘要：無

模型限制：只能根據本次貼文文字與附圖判斷；圖片中的TSM資訊無法確認是否為作者持倉或與貼文主要情緒（BTC損失）相關。

離線一致性／證據提示：[]

與候選比較：與參考強度不同：2 → 3；標的候選集合不同（須按僅提及／持倉／本人立場及圖片待確認分辨，非錯誤判分）

原候選：{"sentiment": "panic", "direction": 1, "strength": 2, "target": "BTC"}

本輪修正候選：{"sentiment": "panic", "direction": 1, "strength": 2, "target": "BTC"}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2165, "input_tokens": 1504, "output_tokens": 661, "reasoning_tokens": 0}}

## 2. threads：threads:3981333267379483868

[來源](https://www.threads.com/@banini31/post/DdAiYM-mXTc) · 2026-09-08T09:45:32+08:00（Asia/Taipei）

原文摘要：爽啦！ 喬喬賺錢了！ 加碼再賺！ 台股簡單啦

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件0張，實際附於生成請求0張；下載成功=False（無附件時為不適用），未人工核圖。

相關性：**investment**。理由：文中提及「賺錢」「加碼」「台股」，明確談及交易與在台股操作，具有投資脈絡。

情緒：**euphoria**；反向方向 **-1**；強度 **2**。理由：文字呈現亢奮與歡呼語氣（「爽啦！」「賺錢了！」「加碼再賺！」），顯示作者對投資結果與繼續買進的積極情緒，情緒明顯但未顯示極端語詞程度。

標的：空白／未辨識；不因而抹除已明確的情緒方向。

本人評論：作者以第一人稱慶祝獲利並表示要加碼，顯示其對台股操作的正面情緒；貼文未提供任何特定標的或代碼，且無附圖可作為標的證據。

第三方引用摘要：無

模型限制：僅根據本則貼文判讀；無附圖、無具體標的或交易數量價格等細節，無法判定作者是否實際持有或交易哪檔股票，也無法量化獲利幅度。

離線一致性／證據提示：[]

與候選比較：標的候選集合不同（須按僅提及／持倉／本人立場及圖片待確認分辨，非錯誤判分）

原候選：{"sentiment": "euphoria", "direction": -1, "strength": 2, "target": "台股"}

本輪修正候選：{"sentiment": "euphoria", "direction": -1, "strength": 2, "target": "台股"}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 1437, "input_tokens": 1063, "output_tokens": 374, "reasoning_tokens": 0}}

## 3. threads：threads:3952464799527950315

[來源](https://www.threads.com/@banini31/post/DbZ-ctLGVfr) · 2026-07-30T13:49:02+08:00（Asia/Taipei）

原文摘要：我還有  原本價值300萬的個股還沒停損 至於主動ETF.. 隨便他了_(:_」∠)_

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件0張，實際附於生成請求0張；下載成功=False（無附件時為不適用），未人工核圖。

相關性：**investment**。理由：作者提及「個股還沒停損」、「主動ETF」等投資相關詞，明確談論持股與處理策略，屬投資脈絡。

情緒：**panic**；反向方向 **1**；強度 **2**。理由：語句表現出無奈與負面情緒（尚未停損、對ETF採放任態度及無力的顏文字），顯示投資上的沮喪或焦慮，屬較明顯的恐慌/無奈情緒但未使用極端字眼。

標的候選及證據：{"name": "個股", "ticker": "", "relationship": "author_stance", "evidence": [{"source": "author_text", "image_index": -1, "quote": "原本價值300萬的個股還沒停損", "sha256": null, "evidence_status": "literal_text_match", "human_verified": false}], "name_supported": true, "ticker_supported": false, "human_verified": false, "status": "text_supported"}

標的候選及證據：{"name": "主動ETF", "ticker": "", "relationship": "author_stance", "evidence": [{"source": "author_text", "image_index": -1, "quote": "至於主動ETF.. 隨便他了_(:_」∠)_", "sha256": null, "evidence_status": "literal_text_match", "human_verified": false}], "name_supported": true, "ticker_supported": false, "human_verified": false, "status": "text_supported"}

本人評論：作者明確談及其持有的個股與主動ETF，語氣顯示無奈與沮喪，推論為投資恐慌情緒。不得使用或推測其他未提供之上下文或圖片。

第三方引用摘要：無

模型限制：僅有一句簡短文字，未提供具體標的名稱或代碼、持倉損益百分比或交易意圖細節；沒有圖片或額外上下文，故無法更精確評估情緒強度或是否將執行停損。

離線一致性／證據提示：[]

與候選比較：與原候選方向不同：0 → 1；與本輪修正候選方向不同：0 → 1；與參考強度不同：1 → 2；情緒類別與原候選不同：neutral → panic；標的候選集合不同（須按僅提及／持倉／本人立場及圖片待確認分辨，非錯誤判分）

原候選：{"sentiment": "neutral", "direction": 0, "strength": 1, "target": ""}

本輪修正候選：{"sentiment": "neutral", "direction": 0, "strength": 1, "target": ""}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 1648, "input_tokens": 1073, "output_tokens": 575, "reasoning_tokens": 0}}

## 4. threads：threads:4024468641932717746

[來源](https://www.threads.com/t/DfZyOhEGS6y) · 2026-11-06T22:07:49+08:00（Asia/Taipei）

原文摘要：沒事， 就是給大家看看我的新GShock 然後跟大家說， 看來下週穩了

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件1張，實際附於生成請求1張；下載成功=True（無附件時為不適用），未人工核圖。
- 下載證據：{"sha256": "d05341342435ce668ab641a4ac7a0ec0cb3172bd5e234891b294b5c5eed24415", "bytes": 628272, "mime": "image/jpeg"}

相關性：**insufficient_information**。理由：貼文內容是在展示新GShock手錶並表示「看來下週穩了」，沒有明確投資標的、買賣或持倉資訊，無法確定為投資相關（可能是生活分享或非金融語境）。

情緒：**insufficient_information**；反向方向 **0**；強度 **1**。理由：文字與圖片主要為生活展示（手錶），僅有一句模糊的『看來下週穩了』，不足以判定為投資相關的亢奮或恐慌情緒。

圖片觀察（服務聲稱）：{"image_index": 0, "readable": true, "observation": "近距離手腕照，顯示一只 G-SHOCK 手錶，藍色錶面及三個小錶盤。背景為淺色衣物或褲料。", "visible_text": "G-SHOCK", "investment_information": false, "limitation": "圖片為生活物品展示，未包含任何股票、代碼或其他投資資訊。"}

標的：空白／未辨識；不因而抹除已明確的情緒方向。

本人評論：

第三方引用摘要：無

模型限制：僅依本次提供的貼文文字與一張圖片判讀；沒有其他上下文或後續貼文，無法推測作者是否在指股票、加密貨幣或其他投資市場，因此將相關性與情緒標為不足資訊。

離線一致性／證據提示：[]

與候選比較：相關性與原無關候選不同：insufficient_information

原候選：{"sentiment": "unrelated", "direction": 0, "strength": 1, "target": ""}

本輪修正候選：{"sentiment": "unrelated", "direction": 0, "strength": 1, "target": ""}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2436, "input_tokens": 1989, "output_tokens": 447, "reasoning_tokens": 0}}

## 5. facebook：facebook:1640562917428297

[來源](https://www.facebook.com/reel/29266616599605070/) · 2026-08-30T23:11:29+08:00（Asia/Taipei）

原文摘要：買欣興，欣興會被警調 買康霈，康霈會⋯  但是投資自己，一定沒有錯！ 因為不管是男人/女人，都有一個愛美的心～ 為了自己而變美，一點都沒錯❤️  這次感謝 宸曜美學 給我這個機會 幫忙評估了我的狀況給出推薦方案 打了我一直想打卻捨不得打得鳳凰電波跟眼周音波🤣 而且還很貼心的用盡各種減痛的方式讓我用到最推薦的功率❤️  每次做完醫美真的覺得 為了變美的你我都是

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：None；schema通過：False；生成嘗試：0。狀態：input_review。

圖片：原附件1張，實際附於生成請求0張；下載成功=False（無附件時為不適用），未人工核圖。

相關性、方向、強度、標的與判讀理由：未取得。錯誤：video_or_unknown_media_requires_review

與候選比較：無答案可比較

原候選：{"sentiment": "unrelated", "direction": 0, "strength": 1, "target": ""}

本輪修正候選：{"sentiment": "unrelated", "direction": 0, "strength": 1, "target": ""}

服務回報：null

## 6. facebook：facebook:1629435205207735

[來源](https://www.facebook.com/DieWithoutBang/posts/pfbid0BaXyVMKvDPkLvQ1uJMQaU7TGmocjZxnvT3Z59xVvEd1XHk9HnbsbBVPFmCCBxBrYl) · 2026-08-18T09:41:59+08:00（Asia/Taipei）

原文摘要：今天穩了！ 大家一起跟我念！ 一天100點，台股5萬點！

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件1張，實際附於生成請求1張；下載成功=True（無附件時為不適用），未人工核圖。
- 下載證據：{"sha256": "b7b30f2f0a21338c9b3b2c623370a90ade9ee152b865001b4bb7de62bd4bdae2", "bytes": 37025, "mime": "image/jpeg"}

相關性：**investment**。理由：貼文內容提到『一天100點，台股5萬點』並附上股票報價畫面，具有明確投資/股市脈絡。

情緒：**euphoria**；反向方向 **-1**；強度 **2**。理由：文字帶有樂觀歡呼語氣（『今天穩了！大家一起跟我念！』）並以強烈目標性語句預期指數上漲（『一天100點，台股5萬點！』），屬投資亢奮情緒。情緒不是極端狂喜但明顯正向。

圖片觀察（服務聲稱）：{"image_index": 0, "readable": true, "observation": "顯示ADR分頁的多檔股票報價截圖，包含中文名稱、價格、漲跌及漲跌幅與對應代碼。", "visible_text": "ADR   台積電 430.97 ▲4.62 ▲1.08% 鴻海 16.21 ▼0.17 ▼1.04% 日月光 39.91 ▲0.37 ▲0.94% 慧榮 272.70 ▲3.80 ▲1.41% 奇景光電 15.41 ▲0.18 ▲1.18% 聯電 19.53 ▲0.38 ▲1.98%", "investment_information": true, "limitation": "圖片為截圖，顯示數檔股票報價但未顯示作者持倉或交易行為；代碼為截圖文字，視為圖片可見資訊。"}

標的候選及證據：{"name": "台積電", "ticker": "TSM", "relationship": "mentioned_only", "evidence": [{"source": "image", "image_index": 0, "quote": "台積電 430.97 ▲4.62 ▲1.08% TSM", "sha256": "b7b30f2f0a21338c9b3b2c623370a90ade9ee152b865001b4bb7de62bd4bdae2", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": true, "ticker_supported": true, "human_verified": false, "status": "pending_human_confirmation"}

標的候選及證據：{"name": "鴻海", "ticker": "HNHFP", "relationship": "mentioned_only", "evidence": [{"source": "image", "image_index": 0, "quote": "鴻海 16.21 ▼0.17 ▼1.04% HNHPF", "sha256": "b7b30f2f0a21338c9b3b2c623370a90ade9ee152b865001b4bb7de62bd4bdae2", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": true, "ticker_supported": false, "human_verified": false, "status": "pending_human_confirmation"}

標的候選及證據：{"name": "日月光", "ticker": "ASX", "relationship": "mentioned_only", "evidence": [{"source": "image", "image_index": 0, "quote": "日月光 39.91 ▲0.37 ▲0.94% ASX", "sha256": "b7b30f2f0a21338c9b3b2c623370a90ade9ee152b865001b4bb7de62bd4bdae2", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": true, "ticker_supported": true, "human_verified": false, "status": "pending_human_confirmation"}

標的候選及證據：{"name": "慧榮", "ticker": "SIMO", "relationship": "mentioned_only", "evidence": [{"source": "image", "image_index": 0, "quote": "慧榮 272.70 ▲3.80 ▲1.41% SIMO", "sha256": "b7b30f2f0a21338c9b3b2c623370a90ade9ee152b865001b4bb7de62bd4bdae2", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": true, "ticker_supported": true, "human_verified": false, "status": "pending_human_confirmation"}

標的候選及證據：{"name": "奇景光電", "ticker": "HIMX", "relationship": "mentioned_only", "evidence": [{"source": "image", "image_index": 0, "quote": "奇景光電 15.41 ▲0.18 ▲1.18% HIMX", "sha256": "b7b30f2f0a21338c9b3b2c623370a90ade9ee152b865001b4bb7de62bd4bdae2", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": true, "ticker_supported": true, "human_verified": false, "status": "pending_human_confirmation"}

標的候選及證據：{"name": "聯電", "ticker": "UMC", "relationship": "mentioned_only", "evidence": [{"source": "image", "image_index": 0, "quote": "聯電 19.53 ▲0.38 ▲1.98% UMC", "sha256": "b7b30f2f0a21338c9b3b2c623370a90ade9ee152b865001b4bb7de62bd4bdae2", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": true, "ticker_supported": true, "human_verified": false, "status": "pending_human_confirmation"}

本人評論：作者以歡呼及目標式口號表達對大盤向上期待，並附上ADR股票報價畫面作為市場情境。

第三方引用摘要：無

模型限制：無其他上下文可確認作者是否持有或交易上述個股；貼文只表達對大盤上漲的樂觀情緒，未提供交易計畫或實際績效數據。

離線一致性／證據提示：["untraceable_target_candidate"]

與候選比較：標的候選集合不同（須按僅提及／持倉／本人立場及圖片待確認分辨，非錯誤判分）

原候選：{"sentiment": "euphoria", "direction": -1, "strength": 2, "target": "台股"}

本輪修正候選：{"sentiment": "euphoria", "direction": -1, "strength": 2, "target": "台股"}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2359, "input_tokens": 1412, "output_tokens": 947, "reasoning_tokens": 0}}

## 7. facebook：facebook:1610126397138616

[來源](https://www.facebook.com/DieWithoutBang/posts/pfbid0ko7MYcc7amyA4Sc9AgTEh4DJkFqjczHmZhhDrazNQPqgSvkEF9JAkLQz8XKVmLMZl) · 2026-07-27T12:05:07+08:00（Asia/Taipei）

原文摘要：今日我的庫存 我好痛苦_(:_」∠)_  為什麼我要貪心買個股⋯ 目前貸款買的部分都是大虧⋯⋯⋯⋯⋯

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件1張，實際附於生成請求1張；下載成功=True（無附件時為不適用），未人工核圖。
- 下載證據：{"sha256": "de460f75d05e47f27aec8de87a360cbe8b94d6d85ada7a5d8b1a1cbe662507a1", "bytes": 28494, "mime": "image/jpeg"}

相關性：**investment**。理由：貼文明確提到「庫存」「貸款買」「個股」「大虧」，描述與投資持股及損失有關。

情緒：**panic**；反向方向 **1**；強度 **3**。理由：作者使用『我好痛苦』『目前貸款買的部分都是大虧』等詞，表達強烈投資痛苦與虧損無奈，屬恐慌/悲觀情緒。

圖片觀察（服務聲稱）：{"image_index": 0, "readable": false, "observation": "螢幕截圖顯示多檔股票的交易資訊欄位（商品、成交、漲跌、幅度），數值與百分比部分可見但商品名稱/代碼被模糊或遮蔽，無法確定具體標的。", "visible_text": "部分百分比數字可見（如 9.91%、9.64%、7.38%、5.86%、5.73%、4.57%），但股票名稱/代碼不可辨認。", "investment_information": true, "limitation": "標的名稱與代碼被模糊或遮蔽，故無法從圖片提取可追溯之具體標的證據。"}

標的候選及證據：{"name": "", "ticker": "", "relationship": "uncertain", "evidence": [{"source": "author_text", "image_index": -1, "quote": "今日我的庫存", "sha256": null, "evidence_status": "literal_text_match", "human_verified": false}, {"source": "image", "image_index": 0, "quote": "圖片含多檔商品名稱欄位，但名稱與代碼被模糊或遮蔽，無法辨識具體標的", "sha256": "de460f75d05e47f27aec8de87a360cbe8b94d6d85ada7a5d8b1a1cbe662507a1", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": false, "ticker_supported": false, "human_verified": false, "status": "pending_human_confirmation"}

本人評論：作者明確表達對持股與貸款槓桿造成的大幅虧損感到痛苦，情緒屬投資恐慌且強烈；圖片為交易畫面但無法辨識具體標的。

第三方引用摘要：無

模型限制：僅使用此貼文文字與一張截圖；未提供可辨識的股票名稱或代碼，且無其他上下文或後續貼文，故無法列出具體標的或進一步評估持股詳情。

離線一致性／證據提示：["image_readability_requires_confirmation"]

與候選比較：與原候選方向不同：0 → 1

原候選：{"sentiment": "panic", "direction": 0, "strength": 1, "target": ""}

本輪修正候選：{"sentiment": "panic", "direction": 1, "strength": 3, "target": ""}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2209, "input_tokens": 1439, "output_tokens": 770, "reasoning_tokens": 0}}

## 8. facebook：facebook:1703774981107090

[來源](https://www.facebook.com/DieWithoutBang/posts/pfbid03143n7ECXc3swjAwzFvjXJFrfksuaecAmRtRR5uV5yaYAvtNQVrh2WDpG1ciUKMXsl) · 2026-11-06T09:15:20+08:00（Asia/Taipei）

原文摘要：市場跟我說 孩子， 你不用停損... 因為你停不掉_(:_」∠)_

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件1張，實際附於生成請求1張；下載成功=True（無附件時為不適用），未人工核圖。
- 下載證據：{"sha256": "b019bdb27af1913d7e35530f2125afad34b530fa093cee97ff53420940f71fcc", "bytes": 34147, "mime": "image/jpeg"}

相關性：**investment**。理由：文字內容提到停損與市場；附圖為交易介面截圖（股價、成交量、時間等），顯示明確投資交易脈絡。

情緒：**panic**；反向方向 **1**；強度 **2**。理由：作者用自嘲語氣表示無法停損，暗含對止損無能為力與挫折感，屬負面投資情緒（恐慌/無奈）。

圖片觀察（服務聲稱）：{"image_index": 0, "readable": true, "observation": "交易介面截圖，顯示股票名稱、代碼、即時價格與時間。左上方顯示股價511.00、下跌56.00（9.88%），畫面中可見名稱「亞翔」與代碼6139。", "visible_text": "511.00 ▼56.00(9.88%) 11/06 09:14:27\n亞翔\n6139", "investment_information": true, "limitation": "截圖為單一時間點畫面，未顯示作者實際買賣數量或持股成本，無法得知損益數字或是否已下單成交。"}

標的候選及證據：{"name": "亞翔", "ticker": "6139", "relationship": "author_stance", "evidence": [{"source": "image", "image_index": 0, "quote": "亞翔", "sha256": "b019bdb27af1913d7e35530f2125afad34b530fa093cee97ff53420940f71fcc", "evidence_status": "pending_human_confirmation", "human_verified": false}, {"source": "image", "image_index": 0, "quote": "6139", "sha256": "b019bdb27af1913d7e35530f2125afad34b530fa093cee97ff53420940f71fcc", "evidence_status": "pending_human_confirmation", "human_verified": false}], "name_supported": true, "ticker_supported": true, "human_verified": false, "status": "pending_human_confirmation"}

本人評論：作者以帶有無奈/自嘲語氣表示自己無法停損，搭配交易介面截圖暗示持有或關注個股（亞翔 6139）並面臨價格下跌情況。

第三方引用摘要：無

模型限制：僅依本則貼文文字與附圖判讀；無其他上下文或後續交易資料，不能確定作者實際持倉數量、成本、是否已下單或更詳細的情緒強度。

離線一致性／證據提示：[]

與候選比較：與原候選方向不同：0 → 1；與本輪修正候選方向不同：0 → 1；與參考強度不同：1 → 2；標的候選集合不同（須按僅提及／持倉／本人立場及圖片待確認分辨，非錯誤判分）

原候選：{"sentiment": "insufficient_information", "direction": 0, "strength": 1, "target": ""}

本輪修正候選：{"sentiment": "insufficient_information", "direction": 0, "strength": 1, "target": ""}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2149, "input_tokens": 1478, "output_tokens": 671, "reasoning_tokens": 0}}

## 9. threads：threads:4023888423198910089

[來源](https://www.threads.com/@banini31/post/DfXuTOQk-aJ) · 2026-11-06T02:55:01+08:00（Asia/Taipei）

原文摘要：恐慌的睡不著

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件0張，實際附於生成請求0張；下載成功=False（無附件時為不適用），未人工核圖。

相關性：**insufficient_information**。理由：貼文僅寫「恐慌的睡不著」，沒有任何投資或財務相關上下文，無法確定是否為投資情緒或生活情緒。

情緒：**insufficient_information**；反向方向 **0**；強度 **1**。理由：文字表達恐慌但未提及投資、持股或交易；依規則情緒判斷需與投資脈絡連結，缺乏該脈絡故無法判定為投資恐慌或亢奮。

標的：空白／未辨識；不因而抹除已明確的情緒方向。

本人評論：該貼文只有一句中文短句，未提供與投資相關的詞彙、標的或圖像，故標的與投資情緒皆無法判定。

第三方引用摘要：無

模型限制：僅使用本次提供之原文與附圖（無附圖）。不得憑外部資訊或推測作者其他貼文或背景。

離線一致性／證據提示：[]

與候選比較：方向／強度／候選標的與提案未見上述差異；非正確性證明

原候選：{"sentiment": "insufficient_information", "direction": 0, "strength": 1, "target": ""}

本輪修正候選：{"sentiment": "insufficient_information", "direction": 0, "strength": 1, "target": ""}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 1359, "input_tokens": 1042, "output_tokens": 317, "reasoning_tokens": 0}}

## 10. threads：threads:3946164126477408639

[來源](https://www.threads.com/@banini31/post/DbDl12IE1l_) · 2026-07-21T21:10:44+08:00（Asia/Taipei）

原文摘要：現在的我呈現一個 因為部分停損，所以大漲不爽 因為還沒損完，所以續跌痛苦 的狀態矛盾狀態_(:_」∠)_  Little sunday 果乾團購： 今日update 因為群創回到50， 獎金變成5萬了❤️  團購連結： 鳳梨真的好吃 https://littlesunday-fruits.my1shop.com/banini

使用上下文：只用本篇原文、同篇引用資料（如有）、實際附圖；沒有其他先前或未來貼文，沒有後續行情。

HTTP：200；schema通過：True；生成嘗試：1。狀態：evaluated_test_only。

圖片：原附件1張，實際附於生成請求1張；下載成功=True（無附件時為不適用），未人工核圖。
- 下載證據：{"sha256": "e69702ef15395a4ac7ddf9c37d60c52ae7c77d4cdfbe2d47df13a9ee964c86b7", "bytes": 2589773, "mime": "image/jpeg"}

相關性：**investment**。理由：貼文明確提到停損、續跌、以及指稱個股「群創回到50」與獎金變化，顯示投資與財務相關情緒與結果。

情緒：**mixed**；反向方向 **0**；強度 **2**。理由：作者同時表達對部分停損導致大漲時不爽（負面/不滿）與為尚未止損而持續下跌感到痛苦（負面/焦慮），呈現矛盾且混合的情緒；語氣清楚但非極端。

圖片觀察（服務聲稱）：{"image_index": 0, "readable": true, "observation": "作者手持Little Sunday 果乾包裝，將果乾靠近嘴巴拍照。包含品牌字樣與包裝外觀可見。畫面為自拍風格人物照。", "visible_text": "Little Sunday", "investment_information": false, "limitation": "圖片顯示商品與作者，但無額外投資或標的代碼資訊；投資情緒來自文字而非圖片。"}

標的候選及證據：{"name": "群創", "ticker": "", "relationship": "author_stance", "evidence": [{"source": "author_text", "image_index": -1, "quote": "因為群創回到50， 獎金變成5萬了❤️", "sha256": null, "evidence_status": "literal_text_match", "human_verified": false}], "name_supported": true, "ticker_supported": false, "human_verified": false, "status": "text_supported"}

本人評論：作者在文中表達因停損與持股續跌所產生的矛盾與痛苦，並提及群創回到價位對獎金的影響，同時推廣果乾團購。

第三方引用摘要：無

模型限制：無明確提供群創之代碼或更多持股細節；圖片與團購連結顯示商品促銷，但與投資情緒無直接視覺證據。

離線一致性／證據提示：[]

與候選比較：與參考強度不同：1 → 2；標的候選集合不同（須按僅提及／持倉／本人立場及圖片待確認分辨，非錯誤判分）

原候選：{"sentiment": "insufficient_information", "direction": 0, "strength": 1, "target": ""}

本輪修正候選：{"sentiment": "insufficient_information", "direction": 0, "strength": 1, "target": ""}

服務回報：{"model_claim": "gpt-5-mini", "reasoning_claim": {"effort": "minimal"}, "format_claim": {"type": "json_schema", "strict": true}, "usage": {"total_tokens": 2602, "input_tokens": 2076, "output_tokens": 526, "reasoning_tokens": 0}}

## 保留限制

第5篇來源附件是Video，不是靜態照片；生成前被擋，沒有影片／音訊分析，也沒有把縮圖當作看完整影片。先前樣本文件把它列於圖片清單不精確；這是來源型態的更正，不更動候選答案。其餘尚未嘗試樣本的續行不重送任何已生成資料，也不改凍結prompt/schema。
這是10篇選定樣本的技術及語意評估，不代表659篇整體品質，也不能證明服務實際模型或視覺推理。舊回應不符合本輪同規則與資料完整要求，未重用為新答案。不得用這輪答案修改候選後再宣稱事前命中。正式archive與Pine未寫入；一般暫停、排程、Pages與PR未合併維持。

## 逐篇審查與差異解讀（生成後，未改寫模型答案）

以下為助手依原貼文文字與保存輸出的複核，不是人工核圖；所有圖片仍標未核實。沒有準確率結論，也沒有用後續行情驗證情緒。

### 樣本 1

- 方向+1與恐慌候選一致；強度由參考2成為3，屬評分分歧。圖片新增TSM報價資訊（服務轉錄），模型正確將其另列僅提及，沒有把BTC痛苦移套TSM；未人工核圖。

### 樣本 2

- 方向-1、強度2與候選一致；未辨識具體標的，與候選台股泛稱不同，但不抹除投資亢奮方向。

### 樣本 3

- 與中性／資訊不足候選分歧：模型判恐慌+1／2。它將未停損及隨便他了當成無奈，可能放寬了恐慌閾值；僅持倉或未停損不能單獨證明恐慌，需人工確認。個股／主動ETF只是泛稱，不等於已辨識具體股票。

### 樣本 4

- 模型採資訊不足／0／1；不是確定無關，但未把生活樂觀硬判交易訊號。圖片描述只增加手錶生活情境，未提供投資證據；未人工核圖。

### 樣本 5

- 附件實際__typename=Video，生成前即阻擋，API請求0、沒有模型答案。未取縮圖冒充看完整影片，未以純文字降級。先前樣本文件將影片列在圖片清單不精確；正式樣本不換篇、不替補。

### 樣本 6

- 方向-1／2與候選一致。可讀行情圖片提供額外投資脈絡及多檔名稱，但只是報價，不代表作者持倉或對每檔表態。
- 已確認的內部矛盾：ticker欄為HNHFP，模型自己的引用證據為HNHPF；這個ticker候選不受其證據支持。未人工核圖，不能藉此確認圖片真正內容，也不採用錯拼代碼。

### 樣本 7

- 三軸分開後：investment、panic、方向+1／強度3；與原方向0候選不同，與發送前修正提案相同，但候選沒有進prompt，不當成事前命中率。
- 本人文字已明確說買個股、貸款部分大虧、好痛苦，足以支持投資痛苦。圖片名稱／代碼被模糊的說法僅為模型描述；標的留空，不降低已確定情緒方向。
- 圖像emotion_evidence的quote包含畫面顯示等描述，並非逐字轉錄，不能當作已核實可見文字。文字證據可單獨支持本輪情緒，圖片只待確認，不宣稱人工核圖。

### 樣本 8

- 與原候選0／1不同，模型判panic、+1／2；理由為無法停損的挫折，並用圖中跌幅補足投資脈絡。
- 新增可追溯的圖片候選亞翔／6139（服務轉錄、圖索引0與SHA256綁定），仍待人工核實。單篇及行情畫面不能證明本人實際持倉、無法停損的原因或恐慌程度；author_stance與情緒閾值需確認，不將API回應自動提升成正式訊號。

### 樣本 9

- 資訊不足／0／1，與候選一致：只有恐慌的睡不著，無投資上下文；不挪用其他先前或未來貼文補理由。

### 樣本 10

- mixed、方向0與候選一致，強度由參考1成為2。圖片僅增加果乾業配情境（服務描述），沒有投資標的視覺證據。
- 標的角色缺乏原文支持：群創位於團購獎金段落，出現股價不能證明作者對該股的投資立場。保留原輸出author_stance供審查，正式候選應待確認，不能因逐字提及就視為立場已證實。

## 結論與執行證據

取得9篇HTTP200、schema有效的模型答案；第5篇Video無答案。判讀品質仍需審查，不能以schema成功推定語意正確，也不解鎖659篇。實際發送6張圖片；3篇原本無附件。圖片是否有投資資訊均是服務描述，不是獨立人工看圖。

第一次執行在第5篇輸入檢查停止；由於前4篇均成功且沒有API／額度異常，只續行原本未嘗試的第6～10篇，不重送任何已有生成，也不重試第5篇。兩次執行合計9次生成、無自動重試，逐筆generation_attempts可稽核。

[首段執行](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42351353197) · [剩餘未嘗試樣本](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42351622396)。前者失敗原因是Video輸入型態，後者成功不代表第5篇已處理完成。兩次各保存audit至GitHub，控制平面另有contents GET／PUT各2次，非供應商查詢。

服務回報合計input 13076、output 5288、total 18364、reasoning_tokens 0。前後免費點數、剩餘請求額度及實際扣點均未取得；不宣稱零扣點，不以tokens估點數。已關閉一次性入口。90項離線測試通過。正式social_posts.json、Pine、其餘歷史與市場快取未改動；一般pause、排程、Pages停用，PR未合併。
