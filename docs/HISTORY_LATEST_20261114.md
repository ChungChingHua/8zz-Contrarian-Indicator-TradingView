# 2026-11-14：最新歷史增量與 AI 額度停止

資料抓取完成至 **2026-11-14T18:21:07.585530+08:00（台灣時間）**。判讀尚未全部補齊，停止原因是 ChatAnywhere 回報目前 24 小時視窗所有免費模型共用 100 次請求已用完。不是本輪 Apify 增量抓取失敗，也不是本地 70 次或 US$0.10 限制。

## 本輪結果

| 項目 | 結果 |
|---|---|
| 抓取 | Facebook 新增 20 篇；Threads 回傳 27 筆，保留本人主貼文 24 篇，排除 3 筆 reply/repost/unknown |
| 新增來源貼文 | 44 篇，原 666 → 710 篇 |
| 生成請求 | 37 次；36 次 HTTP 200 通過固定格式及原規則處理；1 次 HTTP 403 |
| 本輪分類 | 18 有訊號、15 無訊號、3 待確認、1 技術失敗；未重試 |
| 已保存有效回應推進日期 | 2026-11-12 21:59:30（不代表較早所有問題已解決） |
| 本輪 403 貼文 | Threads，2026-11-13 00:56:41；保留 technical_failure，不當作完成 |
| 下一筆本輪未送出 | 2026-11-13 01:45:26 |
| 完整 Pine | 380 → 398 事件；原 151 歷史事件保留、累計 247 新事件 |
| 最新訊號日期 | 2026-11-12T13:48:28+08:00 |
| 全部 710 篇狀態 | 有訊號 249、無訊號 321、待確認 102、技術失敗 14、輸入失敗 7、狀態不明 0、未開始 17 |

來源貼文數與 Pine 事件數的口徑不同；跨平台成員、舊測試與保留的歷史事件不直接一對一。較早待確認／失敗仍列入未完成清單，沒有用最新訊號或較晚單篇日期取代完整處理範圍。

未開始的 17 篇＝10 篇舊 Facebook 缺圖＋7 篇本輪新文章。舊 10 篇關聯到先前 ABORTED run；新限定金鑰讀該舊 run 回 HTTP403，沒有重新啟動該批或繞過權限。程式準備了「已核實終止且零資料」的可追溯例外，但本輪未通過即時查證，因此沒有套用，也沒有重抓已完成內容。

## 抓取範圍、版本及費用

雙平台皆從先前成功截止 2026-11-07 20:15:59.578797 接續，保留兩小時重疊。實際查詢起點為 **11/7 18:15:59.578797**，截止固定為 **11/14 18:21:07.585530**；沒有重抓整段歷史。兩來源 window 都成功完成。

| 平台 | Actor／正式 ID | 版本 | run ID | 回傳筆數 | 最後 API 費用觀察 USD |
|---|---|---|---|---:|---:|
| Facebook | apify/facebook-posts-scraper／KoJrdxJCTtpon81KY | 0.0.421 | 1eDyx3uOHnTVfD5Ln | 20 | 0.14100000000000001 |
| Threads | automation-lab/threads-scraper／yacNYZpu9F3C8EATQ | 0.1.72 | hinVUOAgNEM17Le6K | 27 | 0.155 |

只將每個 run 的 usageTotalUsd 加總一次，合計 **約 US$0.296**；分項與 externalChargedTotalUsd 不重複相加。初次 Threads 回報 0，完成後刷新已變成 0.155，明確不是免費證據。這是 API 費用觀察，不是獨立核對的已結算帳單，仍可能更新。

請求計數：本輪 Apify 憑證驗證 GET2；增量 GET13／POST2；舊媒體只讀 GET1（403，未再查）；費用刷新與帳戶額度 GET3。合計 **GET19／POST2**，共新啟動 2 個 Actor，沒有補抓 Actor。GitHub 檢查／存檔及圖片下載不混入供應商 API 計數。費用 JSON 內 actor_starts=0 指「唯讀費用刷新」本身，本輪抓取啟動數是 2。

帳戶 limits 查詢因限定權限回 HTTP403，Apify 剩餘額度無法取得；未提高帳戶額度、儲值或開放額外權限。

## AI 用量、模型與媒體

- 請求設定：ChatAnywhere https://api.chatanywhere.tech/v1，gpt-5-mini，minimal，strict schema，store=false、無 tools；只用 CHATANYWHERE_API_KEY。
- 服務回傳：成功回應的 model 為 gpt-5-mini，reasoning.effort 為 minimal；只視為服務回報，不宣稱獨立驗證底層模型或實際推理。
- 服務回報 input 98,847／output 5,751／total **104,598 tokens**；reasoning_tokens 回報 0，不等於已驗證沒有推理。HTTP403 無 usage，不能補猜。
- 實際扣點、前後點數、精確免費額度重設時刻未回傳；不把 tokens 當點數，也不宣稱零扣點。服務只明確回報當前 24 小時共用免費請求已用盡，沒有自動重試或付費備援。
- 22 張圖片實際附入請求，其中 21 張所屬回應成功驗證，另 1 張所屬請求回403，不能宣稱該張已完成判讀。圖片來源／hash 與服務觀察保存，沒有宣稱人工核圖。
- 4 筆影片附件未分析，保留文字／實際可讀圖片範圍，不用縮圖冒充影片。
- 不改原作者判讀規則；fingerprint 維持 8ccd8bbe6388705261e7240897417683f2dc6e2016f5db9d5eca462533837162。技術檢查不新增情緒門檻。原始回應與 processed 分開保存。

## 交付、驗證及接續

- [完整指標](../candidates/8zz-history-latest.pine)、[完整策略](../candidates/8zz-strategy-latest.pine)：同 398 事件，packed-v1 round-trip／五欄一致；名稱、同棒最後發文、70 萬本金／保證金門檻、大台1口每點200、買賣各250、ATR設定保留。
- [同版核對資訊](../candidates/8zz-pine-delivery.json)：strategy_default_end_date=2026-11-13。未在 TradingView 實際編譯本版，不宣稱編譯通過。
- [全部未完成清單](../data/history_unresolved_20261114_latest.json)：140 篇，包含舊樣本與待確認／失敗；不把它們當作處理完成。
- [費用快照](../data/history_latest_costs_20261114.json)、[增量帳本](../data/history_latest_acquisition_20261114.json)、[原始回應與結果034](../data/history_progress/history-completion-20261107-034.json)、[035](../data/history_progress/history-completion-20261107-035.json)。
- 雲端執行前後各 265 項離線 unittest 通過；服務異常即保存停止。GitHub 工作流成功表示安全停機／產物保存成功，不代表全部資料判讀完成。
- 快取 artifact history-latest-classified-cache-20261114，run43585240072，2,770,906 bytes，保留至 2026-11-28 18:30:28 台灣時間；含 SHA256／格式驗證位元組與 query-redacted manifest，沒有完整 signed URL 或金鑰。
- 額度恢復後用新授權 session，只續未送出項目；本輪403與其他失敗／待確認／unknown 不自動重送。新貼文抓取從各來源本輪成功截止接續，保留重疊去重。舊缺圖仍需處理存取／確認零資料的證據，不能因此重抓已完成文章。
- TradingView 請各自開啟指標及策略的 Pine Editor，完整取代內容、儲存並更新圖表；GitHub 更新不會自動同步 TradingView。
- 本次入口完成後全停用；沒有持續排程、Telegram、網站發布或合併 PR。

## 本輪逐篇紀錄

以下只使用發文當時的原文與實際附入媒體，context_used 均保留在原始帳本；候選分類沒有放入提示。方向為反向指標方向，0 不產生箭頭。

| 來源 | 台灣發文時間 | 狀態 | HTTP | 方向 | 強度 | 標的 | 附入圖片 | 理由／停止原因 |
|---|---|---|---|---:|---:|---|---:|---|
| [threads:4025550108146350298](https://www.threads.com/t/DfdoH69mTja) | 2026-11-08T09:56:30+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 生活/工作日常，與投資無關，跳過 |
| [facebook:1706036964214225](https://www.facebook.com/DieWithoutBang/posts/pfbid02m7u3hqZJ4gnLco6m85qhvQqDVvfccFgq82X48has3KA7g8zcoLcTDzjWbBpvFG2Jl) | 2026-11-08T10:00:33+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 內容為活動/座位觀察與生活感想，未提及投資或持倉，屬於跳過 |
| [threads:4025972125223971105](https://www.threads.com/t/DffIFE_mWkh) | 2026-11-08T23:54:58+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 生活自拍與閒聊，並非投資相關內容或明確持倉動作，依規則跳過。 |
| [facebook:1707142260770362](https://www.facebook.com/DieWithoutBang/posts/pfbid02ESs9pNvcvdQu5MFTsts6D6o99t7YrbcRqZfv9DamKHgqR6Q9DVa47tFzmA46XQmYl) | 2026-11-09T09:28:06+08:00 | completed_signal | 200 | -1 | 3 | 0050.TW | 1 | 發文語氣亢奮（衝啊）且附上委託/成交截圖顯示已下單，委託單強制強度3，為亢奮追買偏空訊號 |
| [threads:4026272618643056038](https://www.threads.com/t/DfgMZ1TGeWm) | 2026-11-09T09:52:00+08:00 | completed_signal | 200 | 1 | 3 | 0050.TW | 1 | 發文表示錯把買按成賣且附上多筆委託單/全部成交截圖，為真金白銀的交易錯誤且情緒屬於懊惱/痛苦，依規定強度為3，偏多訊號。 |
| [threads:4026296453345914037](https://www.threads.com/t/DfgR0rGGSy1) | 2026-11-09T10:39:21+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 只有非投資的文字／玩笑（招喚小貓），與投資立場無關，依規則跳過 |
| [facebook:1707279274089994](https://www.facebook.com/DieWithoutBang/posts/pfbid02tk6AgSUm2vKzRavguRH9tfsgXSfXbEd7n3uPDjWZmEcUkbQkDVVL3SL44zqjhMGPl) | 2026-11-09T12:36:40+08:00 | completed_signal | 200 | -1 | 3 | 6139.TWO | 1 | 發文帶有懊悔與要把股買回來的念頭，並貼出漲停走勢圖（已漲幅明顯、情緒亢奮），屬於亢奮/追漲心態偏空訊號。 |
| [facebook:1707722754045646](https://www.facebook.com/reel/1152551660798473/) | 2026-11-09T22:16:42+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 內容非投資相關的私人情緒/家庭對話，與交易立場無關，依規則跳過 |
| [threads:4026647813303313518](https://www.threads.com/t/DfhhtojjCRu) | 2026-11-09T22:17:28+08:00 | pending_confirmation | 200 | 0 | 1 |  | 0 | 只有一句話的文字，且附帶影片未分析；無法判定與投資情緒或持倉相關，依規則跳過 |
| [threads:4026685187656644582](https://www.threads.com/t/DfhqNgImffm) | 2026-11-09T23:31:42+08:00 | pending_confirmation | 200 | 0 | 1 |  | 0 | 文字模糊、無具體投資立場或情緒指向，無法判定是否與實際交易或強烈情緒相關，依規則跳過 |
| [facebook:1707830474034874](https://www.facebook.com/DieWithoutBang/posts/pfbid0PiwmoP3UGkbYmUQF5gbMLWrQ8jdqwYyJBTPMfhK8dDLpH6x7UxaeW5vmMdRekGHEl) | 2026-11-10T00:20:19+08:00 | completed_signal | 200 | 1 | 3 |  | 1 | 列出多檔美股且配上未實現大幅虧損截圖，情緒為痛苦/被套，偏多訊號 |
| [threads:4026780710220697727](https://www.threads.com/t/Dfh_7idGZB_) | 2026-11-10T02:41:29+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 表述為持有現金比例與資金狀況，語氣中性且無明確交易情緒或決策訊號，屬於被動描述，跳過 |
| [facebook:1708163567334898](https://www.facebook.com/DieWithoutBang/posts/pfbid024fr4J8Lkq5vTq1GMep5WeRaxYtZCUg63JuJLVuR6ZyDjPreiyQoQ2wAhYGKbbuY9l) | 2026-11-10T08:27:07+08:00 | completed_signal | 200 | -1 | 2 |  | 1 | 語氣看似看好大盤並興奮描述漲勢（亢奮/追漲傾向），屬於偏空訊號 |
| [facebook:1708197577331497](https://www.facebook.com/DieWithoutBang/posts/pfbid022LyMy4tC8jXHdDX9Wy8eLmb68k4MwxkADM8RGfu57Yuemer9E2BEMmM4fFTnkS4ol) | 2026-11-10T09:19:52+08:00 | completed_signal | 200 | -1 | 3 | 0050.TW | 1 | 附有委託單截圖且顯示元大台灣50全部成交，已真金白銀下單且情緒偏向亢奮/積極追買，強度強制為3 |
| [threads:4027013070392517757](https://www.threads.com/t/Dfi0w0umeR9) | 2026-11-10T10:23:08+08:00 | completed_signal | 200 | -1 | 2 |  | 0 | 宣布結束大力補倉並轉回小額個股，語氣較有把握與自信，偏向主動操作與樂觀，屬於偏空訊號（亢奮/自信） |
| [threads:4027027180417050470](https://www.threads.com/t/Dfi3-Jtmedm) | 2026-11-10T10:51:10+08:00 | completed_signal | 200 | 1 | 3 |  | 0 | 發文者強烈恐慌且情緒激動（買很多但台股下跌造成痛苦），屬於被套/恐慌情緒，偏多訊號。 |
| [threads:4027056616092826145](https://www.threads.com/t/Dfi-qf0mXoh) | 2026-11-10T11:49:39+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 僅表達對台股的感嘆，無明確持倉或交易動作，屬與投資無關或情緒模糊的貼文，跳過 |
| [facebook:1708750210609567](https://www.facebook.com/reel/1598584782020837/) | 2026-11-10T21:21:12+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 僅為對AI使用的評論／控訴，無明確個人持倉或交易情緒，屬非投資貼文需跳過 |
| [threads:4027405115971988012](https://www.threads.com/t/DfkN51oGeos) | 2026-11-10T23:22:04+08:00 | completed_signal | 200 | -1 | 2 |  | 0 | 短句只表達亢奮的買入情緒（FOMO/喊衝）但無特定標的或實際下單證據，屬於偏空亢奮訊號 |
| [threads:4027439123892129807](https://www.threads.com/t/DfkVot-GdAP) | 2026-11-11T00:29:38+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 發文表示想去買手錶、無投資立場或交易意圖，屬生活消費貼文，跳過 |
| [threads:4027509015852588961](https://www.threads.com/t/Dfklhx7k5-h) | 2026-11-11T02:48:30+08:00 | completed_signal | 200 | 1 | 3 |  | 0 | 發文者表示資金吃緊、痛苦且懇求別再下跌，情緒為恐慌被套/無錢，偏多訊號 |
| [facebook:1709288087222446](https://www.facebook.com/DieWithoutBang/posts/pfbid0DZsAxC18eVZHafJ8vf5yyDh4okAQ6LZHFmKKm4MZEa33s3a1CZD9a65vAymMHoabl) | 2026-11-11T08:39:49+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 主要是生活/焦慮與流量相關抱怨，並無明確投資動作或情緒立場，屬於跳過。 |
| [facebook:1709341027217152](https://www.facebook.com/DieWithoutBang/posts/pfbid02DbwSKaob1p7ct11zPsXC23tYkxQaJMhvfSe3cRXCsi3eK7GD5gAWoNH3Mw33VKqtl) | 2026-11-11T10:08:05+08:00 | completed_signal | 200 | 1 | 3 |  | 1 | 發文表達放棄個股改買指數/正二，情緒為失望/撤退；且附圖顯示委託全部成交（真金白銀下單），強度強制為3，偏多（痛苦/撤退）訊號。 |
| [threads:4027793267760924866](https://www.threads.com/t/DflmKMJmYjC) | 2026-11-11T12:13:15+08:00 | completed_signal | 200 | 1 | 2 | 0050.TW | 1 | 貼出持有（元大台灣50）且情緒短文 'ekkkkkkk' 顯示不安/挫折感，為痛苦偏多傾向 |
| [facebook:1709445763873345](https://www.facebook.com/DieWithoutBang/posts/pfbid05qn1JeKqYgi8PrWa3Yjm1QE4S1BKBWWbQccncoqk49tWZsWZH649yjL18hdd3pbql) | 2026-11-11T12:14:41+08:00 | completed_signal | 200 | -1 | 2 | 0050.TW | 1 | 表示買了熟悉的981和0050且對漲幅感到興奮（“我好抖”），情緒偏向亢奮/得意，屬於偏空訊號。 |
| [threads:4027848978889003863](https://www.threads.com/t/Dfly05LmVNX) | 2026-11-11T14:03:56+08:00 | completed_signal | 200 | 1 | 3 |  | 0 | 描述因未停損導致巨額虧損由20萬降至7萬，表示強烈痛苦與後悔情緒，屬於偏多（被套/痛苦）訊號 |
| [threads:4027935237988803561](https://www.threads.com/t/DfmGcIOmePp) | 2026-11-11T16:55:19+08:00 | pending_confirmation | 200 | 0 | 1 |  | 0 | 只是表示投入比例過高並在思考調整，情緒與投資立場不明確，需更多資訊判定 |
| [facebook:1710065987144656](https://www.facebook.com/DieWithoutBang/posts/pfbid02emCqMda9tX6Vqa2oTFHGyLU9Nuiq9RqodsBkNYBvEWt7RZ94E5tqyurgzaKpmRfPl) | 2026-11-12T01:11:27+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 生活開箱與炫錶，明確表示“股票？談什麼股票？那東西不是就是一直漲的嗎”屬於非投資立場或閒聊，跳過。 |
| [threads:4028185869932717304](https://www.threads.com/t/Dfm_bTalmT4) | 2026-11-12T01:13:19+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 內容以生活開箱為主，並未明確表達個人持倉或交易情緒，屬於與投資無關或模糊貼文，跳過 |
| [facebook:1710452580439330](https://www.facebook.com/DieWithoutBang/posts/pfbid02Qi4U6vELYD1vfdEPUi5cdNbU6f4xf8U6kXxUVwCU9FwPSiC76NXCzEX8zRUSxVbZl) | 2026-11-12T10:24:01+08:00 | completed_signal | 200 | 1 | 2 |  | 1 | 貼文語氣哀嘆、驚訝並帶悲傷表情，顯示發文者對指數下跌感到痛苦或被套，偏多（恐慌/痛苦）情緒。 |
| [facebook:1710543473763574](https://www.facebook.com/DieWithoutBang/posts/pfbid02CG5AP5gH66y44unMA4WQPRQ71qYCQQSoMT5L2FnwrgdKkYctU7pXrtoi9N3sDPnml) | 2026-11-12T12:33:42+08:00 | completed_signal | 200 | 1 | 2 | 00981.TW | 1 | 發文語氣帶失落（被渣、失望）且貼出個股走勢截圖，顯示為被套或反彈未續，屬於痛苦偏多訊號 |
| [threads:4028531458973464504](https://www.threads.com/t/DfoOASSmXe4) | 2026-11-12T12:39:54+08:00 | completed_signal | 200 | -1 | 3 | NVDA | 1 | 附上成交截圖（Filled）顯示已買入NVIDIA，為亢奮/急速下單行為，依規定強度設為3且偏空（追買情緒）。 |
| [threads:4028565970327512929](https://www.threads.com/t/DfoV2ffmSdh) | 2026-11-12T13:48:28+08:00 | completed_signal | 200 | -1 | 3 | 3711.TW | 1 | 發文情緒極度亢奮（大回血、會更好），並附委託單且全部成交，強度強制為3，屬於FOMO追買偏空訊號 |
| [facebook:1710903840394204](https://www.facebook.com/DieWithoutBang/posts/pfbid02un9yDuaoe39bo8RKwQbEKmvqrXYDC4fZAFBMD2WxT3MS5KRHQ8H6rAHEEcpdywLcl) | 2026-11-12T20:35:57+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 抱怨被爆料與情緒宣洩，未談及個人持倉或交易動作，屬於與投資決策無關的內容，跳過 |
| [threads:4028773206264440076](https://www.threads.com/t/DfpE-LAAOUM) | 2026-11-12T20:40:13+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 貼文內容為抱怨/情緒表達與漫畫分享，未提及任何投資持倉或交易動作，與投資決策無關。 |
| [facebook:1710977397053515](https://www.facebook.com/DieWithoutBang/posts/pfbid02NbXWbXRCuf6TFrxZWKowNVCLcR6cK2PN4JC2k1SuEcfEUgTPH7mtN8JfPjHGjZ2zl) | 2026-11-12T21:59:30+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 轉貼/評論名人新聞且無明確表示個人投資立場或持倉，與投資情緒無關，跳過 |
| [threads:4028902292942561181](https://www.threads.com/t/DfpiUoVmR-d) | 2026-11-13T00:56:41+08:00 | technical_failure | 403 | — | — |  | 1 | provider_http_error |
| [facebook:1711187147032540](https://www.facebook.com/DieWithoutBang/posts/pfbid02AWHj3RuRgtZPvdPiZkQwGfqRJhW81qiAuGixwBpQU2vtVfHMgVUPHRCasqR3aizjl) | 2026-11-13T01:45:26+08:00 | not_started | — | — | — |  | — | 未送出 |
| [facebook:1711452657005989](https://www.facebook.com/DieWithoutBang/posts/pfbid0T1BsmxWfpEE1oFUqCu4uEmWFRzgJq3hn6BQvCEehmrG9wLHQTU3pLLqhWQN7HakSl) | 2026-11-13T07:57:41+08:00 | not_started | — | — | — |  | — | 未送出 |
| [facebook:1711515410333047](https://www.facebook.com/DieWithoutBang/posts/pfbid026b8bNeR6qcGWSBSSCyUysr6UfAmAPDz9wfjbtzjnUMFjsfUNHKbLyNV6jva3d8yYl) | 2026-11-13T09:25:09+08:00 | not_started | — | — | — |  | — | 未送出 |
| [facebook:1712186250265963](https://www.facebook.com/reel/2160900154802469/) | 2026-11-13T23:21:14+08:00 | not_started | — | — | — |  | — | 未送出 |
| [threads:4029579593664549218](https://www.threads.com/t/Dfr8UpyidFi) | 2026-11-13T23:22:24+08:00 | not_started | — | — | — |  | — | 未送出 |
| [threads:4029622132984581375](https://www.threads.com/t/DfsF_rnmQz_) | 2026-11-14T00:46:53+08:00 | not_started | — | — | — |  | — | 未送出 |
| [threads:4029927973335964218](https://www.threads.com/t/DftLiPpGZo6) | 2026-11-14T10:54:32+08:00 | not_started | — | — | — |  | — | 未送出 |
