# 判讀品質候選樣本：10 篇（尚待確認）

本輪只讀既有 archive，沒有模型、圖片下載或其他供應商 API 請求。原文逐字保存；圖片以下方原貼文／公開照片連結與索引列出。現有資料只有部分平台 OCR，本輪未人工看圖，**OCR 不代表圖片已核實**。涉及圖片的預期答案都需先核圖，這份不是已確認的黃金答案。

只採各篇發文當下的文字與附圖；不看之後貼文、網友留言、價格快取或績效，日期只用於識別原貼文。方向 +1 是恐慌的反向訊號，-1 是亢奮的反向訊號；0 不產生訊號。確定中性／無關、資訊不足及技術失敗分開。

中性持倉樣本刻意保留「隨便他了」的邊界：不能為湊滿類別而假稱已確認中性。使用者已同意這10篇做最多10次生成的品質測試；候選答案不是標準答案，不放入模型提示。

| # | 類別 | 來源 | 預期方向 | 候選標的 | 圖片數 |
| --- | --- | --- | ---: | --- | ---: |
| 1 | 明確恐慌 | facebook | 1 | BTC | 1 |
| 2 | 明確亢奮 | threads | -1 | 台股 | 0 |
| 3 | 中性持倉邊界 | threads | 0 | 空白 | 0 |
| 4 | 生活玩笑／既有 smoke | threads | 0 | 空白 | 1 |
| 5 | 生活業配、股票名稱干擾 | facebook | 0 | 空白 | 1 |
| 6 | 投資亢奮＋行情圖片候選 | facebook | -1 | 台股 | 1 |
| 7 | 恐慌＋庫存圖片資訊缺口 | facebook | 1 | 空白 | 1 |
| 8 | 單篇上下文不足／既有 smoke | facebook | 0 | 空白 | 1 |
| 9 | 情緒強烈但投資情境不足 | threads | 0 | 空白 | 0 |
| 10 | 矛盾情緒＋業配及獎金股價 | threads | 0 | 空白 | 1 |

## 1. 明確恐慌

[原貼文](https://www.facebook.com/DieWithoutBang/posts/pfbid0euW28fo5eBPr4X7SsmhcDaoVxD1Un5iz7SkPvY23szM8j9mV73JoHmcVgzw8xs5el) · `facebook:1696581131826475` · 2026-10-30T08:05:00+08:00（Asia/Taipei）

原文：

> 連我的BTC單都沒了
> 這一波應該⋯ 狠恐怖
> 感覺比七月的還猛_(:_」∠)_
>
> 大家風控要做好， 該停損停損啊

預期：方向 **1**、參考強度 2；標的 **BTC**，ticker **空白**。候選決策：`signal / insufficient_information`。

本人說 BTC 單沒了、這波很恐怖，並提醒停損；恐慌情緒的反向方向為 +1，不因之後漲跌改標。BTC 逐字在原文。尚須核對圖片是否引入矛盾。

- [圖片 1／原貼文檢視](https://www.facebook.com/photo/?fbid=1696580331826555)；類型 Photo；media ID `1696580331826555`。本輪未下載、未人工核圖。
  平台 OCR／alt（未驗證）：May be an image of text

## 2. 明確亢奮

[原貼文](https://www.threads.com/@banini31/post/DdAiYM-mXTc) · `threads:3981333267379483868` · 2026-09-08T09:45:32+08:00（Asia/Taipei）

原文：

> 爽啦！ 喬喬賺錢了！
> 加碼再賺！
> 台股簡單啦

預期：方向 **-1**、參考強度 2；標的 **台股**，ticker **空白**。候選決策：`signal`。

本人「爽啦」「加碼再賺」「台股簡單啦」是明確投資歡呼，反向方向 -1；台股在原文，不能把喬喬猜成特定股票代號。

圖片：無附件。

## 3. 中性持倉邊界

[原貼文](https://www.threads.com/@banini31/post/DbZ-ctLGVfr) · `threads:3952464799527950315` · 2026-07-30T13:49:02+08:00（Asia/Taipei）

原文：

> 我還有
>
> 原本價值300萬的個股還沒停損
> 至於主動ETF.. 隨便他了_(:_」∠)_

預期：方向 **0**、參考強度 1；標的 **空白**，ticker **空白**。候選決策：`neutral / insufficient_information`。

原文報告個股及主動 ETF 未停損，未描述明確恐慌或亢奮；持有／未停損本身不是情緒訊號。「隨便他了」也可能是無奈，故中性只是候選，確認前亦接受資訊不足；不猜 ETF 代號。

圖片：無附件。

## 4. 生活玩笑／既有 smoke

[原貼文](https://www.threads.com/t/DfZyOhEGS6y) · `threads:4024468641932717746` · 2026-11-06T22:07:49+08:00（Asia/Taipei）

原文：

> 沒事， 就是給大家看看我的新GShock
> 然後跟大家說， 看來下週穩了

預期：方向 **0**、參考強度 1；標的 **空白**，ticker **空白**。候選決策：`unrelated / insufficient_information`。

新 GShock 與「下週穩了」未提供投資情境或標的。舊服務描述圖片是手錶，但本輪未人工看圖；圖片若確為生活物品，確定無關，否則保留資訊不足，不能硬判看多。

- [圖片 1／原貼文檢視](https://www.threads.com/t/DfZyOhEGS6y)；類型 photo；media ID `未提供`。本輪未下載、未人工核圖。

## 5. 生活業配、股票名稱干擾

[原貼文](https://www.facebook.com/reel/29266616599605070/) · `facebook:1640562917428297` · 2026-08-30T23:11:29+08:00（Asia/Taipei）

原文：

> 買欣興，欣興會被警調
> 買康霈，康霈會⋯
>
> 但是投資自己，一定沒有錯！
> 因為不管是男人/女人，都有一個愛美的心～
> 為了自己而變美，一點都沒錯❤️
>
> 這次感謝 宸曜美學 給我這個機會
> 幫忙評估了我的狀況給出推薦方案
> 打了我一直想打卻捨不得打得鳳凰電波跟眼周音波🤣
> 而且還很貼心的用盡各種減痛的方式讓我用到最推薦的功率❤️
>
> 每次做完醫美真的覺得
> 為了變美的你我都是勇士⋯🤣
>
> #業配  #說我是巴逆逆派來的
> #台北市醫美 #宸曜美學

預期：方向 **0**、參考強度 1；標的 **空白**，ticker **空白**。候選決策：`unrelated / insufficient_information`。

主題為醫美業配與投資自己；欣興、康霈只是引子，沒有本人明確交易情緒或立場。不能因出現股票名就輸出這兩檔訊號。附圖待核。

- [圖片 1／原貼文檢視](https://www.facebook.com/reel/29266616599605070/)；類型 Video；media ID `29266616599605070`。本輪未下載、未人工核圖。

## 6. 投資亢奮＋行情圖片候選

[原貼文](https://www.facebook.com/DieWithoutBang/posts/pfbid0BaXyVMKvDPkLvQ1uJMQaU7TGmocjZxnvT3Z59xVvEd1XHk9HnbsbBVPFmCCBxBrYl) · `facebook:1629435205207735` · 2026-08-18T09:41:59+08:00（Asia/Taipei）

原文：

> 今天穩了！
> 大家一起跟我念！ 一天100點，台股5萬點！

預期：方向 **-1**、參考強度 2；標的 **台股**，ticker **空白**。候選決策：`signal / insufficient_information`。

本人「今天穩了」「一天100點、台股5萬點」是台股亢奮。平台 OCR 顯示 ADR 報價表，屬待人工核對的交易資訊圖片候選；即使表中有多檔，也不能把每檔變成評論標的，不能用後來漲跌作答案。

- [圖片 1／原貼文檢視](https://www.facebook.com/photo/?fbid=1629434968541092)；類型 Photo；media ID `1629434968541092`。本輪未下載、未人工核圖。
  平台 OCR／alt（未驗證）：May be an image of text that says '外匯 美股 港股 福深股 原物料 ADR 加密貨幣 距離台股開盤還有19分鐘 股名/股號 股號 股價 更新 台積電 TSM 漲跌漲跌幅（%） 漲跌幅（%） 漲跌 430.97 4.62 鴻海 HNHPF 1.08% 16.21 0.17 日月光 ASX 1.04% 39.91 0.37 慧榮 SIMO 0.94% 272.70 3.80 奇景光電 HIMX 1.41% 15.41 0.18 聯電 UMC 1.18% 19.53 0.38 1.98%'

## 7. 恐慌＋庫存圖片資訊缺口

[原貼文](https://www.facebook.com/DieWithoutBang/posts/pfbid0ko7MYcc7amyA4Sc9AgTEh4DJkFqjczHmZhhDrazNQPqgSvkEF9JAkLQz8XKVmLMZl) · `facebook:1610126397138616` · 2026-07-27T12:05:07+08:00（Asia/Taipei）

原文：

> 今日我的庫存
> 我好痛苦_(:_」∠)_ 
> 為什麼我要貪心買個股⋯
> 目前貸款買的部分都是大虧⋯⋯⋯⋯⋯

預期：方向 **1**、參考強度 3；標的 **空白**，ticker **空白**。候選決策：`insufficient_information`。

文字「今日我的庫存」「好痛苦」「貸款買的部分都是大虧」支持強烈投資痛苦，但未提供單一標的。平台未提供可讀圖片描述，本輪未人工核圖，不能宣稱圖內確有庫存或從中猜標的；即使圖內有多檔持股也不等於對每檔表態。相關性、情緒與標的分開：投資痛苦明確，候選反向方向+1、強度3；標的空白或待核圖不會使情緒歸零。

- [圖片 1／原貼文檢視](https://www.facebook.com/photo/?fbid=1610126383805284)；類型 Photo；media ID `1610126383805284`。本輪未下載、未人工核圖。
  平台 OCR／alt（未驗證）：No photo description available.

## 8. 單篇上下文不足／既有 smoke

[原貼文](https://www.facebook.com/DieWithoutBang/posts/pfbid03143n7ECXc3swjAwzFvjXJFrfksuaecAmRtRR5uV5yaYAvtNQVrh2WDpG1ciUKMXsl) · `facebook:1703774981107090` · 2026-11-06T09:15:20+08:00（Asia/Taipei）

原文：

> 市場跟我說
> 孩子， 你不用停損...
> 因為你停不掉_(:_」∠)_

預期：方向 **0**、參考強度 1；標的 **空白**，ticker **空白**。候選決策：`insufficient_information`。

「不用停損、因為停不掉」可能為自嘲或流動性等問題，不能單憑字眼斷定恐慌強度。亞翔／6139 不在原文，舊模型答案沒有可追溯圖片文字證據，須留空。「市場跟我說」是修辭，不當作第三方文章。

- [圖片 1／原貼文檢視](https://www.facebook.com/photo/?fbid=1703774447773810)；類型 Photo；media ID `1703774447773810`。本輪未下載、未人工核圖。
  平台 OCR／alt（未驗證）：May be an image of text

## 9. 情緒強烈但投資情境不足

[原貼文](https://www.threads.com/@banini31/post/DfXuTOQk-aJ) · `threads:4023888423198910089` · 2026-11-06T02:55:01+08:00（Asia/Taipei）

原文：

> 恐慌的睡不著

預期：方向 **0**、參考強度 1；標的 **空白**，ticker **空白**。候選決策：`insufficient_information`。

只有「恐慌的睡不著」，無圖片、無標的或投資情境。不能讀鄰近／之後貼文把恐慌原因補成股票；也不能肯定無關，應為資訊不足。

圖片：無附件。

## 10. 矛盾情緒＋業配及獎金股價

[原貼文](https://www.threads.com/@banini31/post/DbDl12IE1l_) · `threads:3946164126477408639` · 2026-07-21T21:10:44+08:00（Asia/Taipei）

原文：

> 現在的我呈現一個
> 因為部分停損，所以大漲不爽
> 因為還沒損完，所以續跌痛苦
> 的狀態矛盾狀態_(:_」∠)_
>
> Little sunday 果乾團購： 今日update
> 因為群創回到50， 獎金變成5萬了❤️
>
> 團購連結： 鳳梨真的好吃
> https://littlesunday-fruits.my1shop.com/banini

預期：方向 **0**、參考強度 1；標的 **空白**，ticker **空白**。候選決策：`insufficient_information`。

本人明說漲不爽、跌痛苦的矛盾情緒；群創股價在果乾團購獎金段落，不足以指定為本人交易立場標的。先區分本人情緒與業配，方向0，不以群創之後表現決定。

- [圖片 1／原貼文檢視](https://www.threads.com/@banini31/post/DbDl12IE1l_)；類型 image；media ID `未提供`。本輪未下載、未人工核圖。

本輪品質測試結果只存測試紀錄，無 API 答案不標記完成。不得把供應商技術成功當成語意標籤正確，亦不批次／排程／Pages／合併。
