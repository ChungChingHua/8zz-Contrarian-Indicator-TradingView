# 2026-11-15：未送出資料接續與缺圖補齊

本次資料抓取完成至台灣時間 **2026-11-15 16:55:04.406470**，717篇保存貼文的「尚未開始」已為 **0**。不是所有分類均已結案：仍有105待確認、15技術失敗、7輸入失敗，共127篇保留，不轉成訊號、不默默視為完成，unknown為0。

## 實際進度

- 雙平台從11/14 18:21:07.585530成功截止接續；兩小時重疊後，實際查詢起點11/14 16:21:07.585530，截止固定11/15 16:55:04.406470。Facebook新增2、Threads新增5，710→717篇。沒有重抓整段歷史。
- 第一階段只續原7篇未送出＋7篇新文章，14次HTTP200，13篇通過完整驗證：1訊號、10無訊號、2待確認；另1篇invalid_ticker_format保留技術失敗，原始回應存在，不重送。
- 第二階段解決舊10篇Facebook缺圖：10篇均取得新圖片、一次判讀各一篇，10次HTTP200全部通過完整驗證：6訊號、3無訊號、1待確認。
- 共24次生成、24次HTTP200、23篇通過驗證；7訊號、13無訊號、3待確認、1技術失敗。原先完成、舊待確認、舊失敗及先前測試未重新生成。
- 完整指標／策略398→**405事件**；原398個五欄tuple逐筆保留，新增7筆，兩份405個事件五欄完全一致。原作者151歷史事件保留，累計254新增事件。
- 最新訊號：**2026-11-15 10:33:27**；最新已保存有效回應所對應發文：**2026-11-15 15:31:11**。這些時間不取代抓取截止。較早待確認／失敗仍存在，不宣稱所有文章判讀完成。

| 全部717篇保存貼文狀態 | 篇數 |
|---|---:|
| 有訊號 | 256 |
| 無訊號 | 334 |
| 待確認 | 105 |
| 技術失敗 | 15 |
| 輸入失敗 | 7 |
| 狀態不明 | 0 |
| 尚未開始 | 0 |

貼文數包含跨平台成員，事件數還包含原歷史，兩者不是一對一。

## 舊缺圖修復證據與去重

舊金鑰範圍無法讀取先前run的403沒有被繞過，也沒有再次查詢該被拒絕端點。本輪使用固定commit c137481646469c46b42fde0ac2151c04181c9a14內的官方API保存回應：原run aN1ESUqN4kVceCqBH已記錄ABORTED、finishedAt存在、dataset itemCount及cleanItemCount均0、post計費事件0。檔案data/history_media_repairs/budget-audit-20261114.json的SHA256為be681da028b6c31e39ecb6db9247ceb396e94de109312dadac0be591aa30e4d5；程式先核對hash與上述欄位，再確認10篇均未送出、不是完成／review／unknown，才保存新授權系譜並開始定向補抓。

這是**離線核驗過去官方回應的證據**，provider觀察時間2026-11-14 15:06:12.077588台灣時間，不冒充今天即時讀取舊run的結果。不是重送狀態不明請求，也沒有放寬unknown／非空資料集的阻擋。新run xPpzRUxhRvhRbi0Td只涵蓋10篇缺媒體貼文，10篇均cached；新舊run與證據關聯保存於20261115-media-repair-02帳本，後續去重索引採最新已核實run，避免再次啟動相同網址。

既有7篇未送出的圖片從前次artifact還原，SHA256／MIME／檔案邊界驗證後才使用；對已抓取的增量文章，快取不可用時隔離，不再另啟Actor重抓。

## 供應商請求、費用及用量

| 工作 | Actor及實際版本 | run ID | 最新usageTotalUsd |
|---|---|---|---:|
| Facebook增量2篇 | apify/facebook-posts-scraper，0.0.421 | 7XocIieNSafu8En1Q | 0.015 |
| Threads增量5篇 | automation-lab/threads-scraper，0.1.74 | c37pGgiCfqvBLdZmv | 0.045 |
| Facebook缺媒體10篇 | apify/facebook-posts-scraper，0.0.421 | xPpzRUxhRvhRbi0Td | 0.051000000000000004 |

每個run的usageTotalUsd只加一次，合計**約US$0.111**（API原值0.111000000000000004）。分項／externalChargedTotalUsd不重複相加；這是API費用觀察，不是獨立結算帳單，仍可能更新。原中止run的舊啟動費不是本輪費用，不再加入。

本輪Apify共**GET20／POST3**＝增量GET8／POST2＋增量費用刷新GET2＋媒體GET7／POST1＋最終費用刷新GET3。實際啟動3個Actor；費用帳本actor_starts=0僅指唯讀刷新自身沒有啟動，不能當成本輪啟動總數。GitHub讀寫與圖片下載另外計數，不混入供應商API數量。既有拒絕的帳戶limits端點不再查，剩餘Apify額度未知。沒有提高帳戶限制、儲值或切換付費服務。

AI生成24次，無模型清單或其他AI查詢，無自動重試。服務回報input **70,152**／output **3,845**／total **73,997 tokens**，包含格式未通過的1篇；reasoning_tokens均回報0，不據此宣稱沒有實際推理。前後免費點數、實際扣點、剩餘請求額度及重設時刻未回傳，均未知，不把點數當tokens、不宣稱零扣點。昨天的100次用盡觀察已移入歷史，不把它冒充本輪仍然額度耗盡。

請求設定：ChatAnywhere .tech/v1、gpt-5-mini、minimal、strict schema、store=false、無工具，只用CHATANYWHERE_API_KEY。24份回應的model均為gpt-5-mini、reasoning.effort均為minimal，僅標示服務回報，不宣稱獨立驗證底層模型或實際推理；沒有官方OpenAI金鑰備援。

實際附入17張圖片，其中16張所屬回應通過完整驗證；另1張所屬回應HTTP200但ticker格式未通過，不將該篇標為完成。4筆影片附件未分析，保留文字／實際圖片範圍，不用縮圖冒充影片；圖片沒有宣稱人工核實。所有context_used為空，只用各篇當時原文與圖片，沒有使用未來貼文或後續行情。

## 交付與檢查

- [完整指標](../candidates/8zz-history-latest.pine)及[完整策略](../candidates/8zz-strategy-latest.pine)：405事件，原398事件逐筆保留、兩份五欄相同、packed-v1 round-trip通過；保留作者及MPL-2.0。
- 策略品質門檻0～100（含等號、0不限制）保留，只篩新倉，不阻擋出場。大台本金／開倉門檻70萬、1口、每點200、買賣各250、同棒最後發文及ATR規則保留，AI情緒規則fingerprint未改。
- [全部127篇未結案清單](../data/history_unresolved_20261115.json)包含舊測試／review／失敗，沒有重寫原始回應或默默視為完成。新增技術失敗facebook:1711515410333047，11/13 09:25:09，HTTP200，invalid_ticker_format；保留原始模型回應，可後續離線檢視，不自行重新生成。
- [總帳本](../data/history_completion_summary.json)、[原始回應036](../data/history_progress/history-completion-20261107-036.json)、[037](../data/history_progress/history-completion-20261107-037.json)、[費用快照](../data/history_latest_costs_20261115_final.json)、[交付SHA與405事件核對](../candidates/8zz-pine-delivery.json)。
- 線上前後離線回歸通過，第二階段及最終完整結果各275項測試通過；另核對原398事件全部保留、兩份405相等及品質門檻存在。未在TradingView實際編譯本版，不宣稱編譯通過。
- 已完成本次範圍所有未送出項目的初次處理，並停止；保留105待確認、15技術失敗、7輸入失敗，仍非所有分類結案。未來新抓取從本輪各平台成功截止接續，兩小時重疊去重；review／failure／unknown不自動重送。
- 更新TradingView仍需分別複製指標及策略全文至Pine Editor、儲存並更新圖表；GitHub不會自動同步。
- 本次入口完成後停用；沒有持續排程、Telegram、網站發布或PR合併。

## 本輪逐篇紀錄

| 來源 | 台灣發文時間 | 狀態 | HTTP | 方向 | 強度 | 標的 | 附入圖片 | 理由／錯誤 |
|---|---|---|---|---:|---:|---|---:|---|
| [facebook:1711187147032540](https://www.facebook.com/DieWithoutBang/posts/pfbid02AWHj3RuRgtZPvdPiZkQwGfqRJhW81qiAuGixwBpQU2vtVfHMgVUPHRCasqR3aizjl) | 2026-11-13T01:45:26+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 內容以生活與經營社群、情緒抱怨為主，沒有明確投資動作或強烈投資情緒，屬於跳過。 |
| [facebook:1711452657005989](https://www.facebook.com/DieWithoutBang/posts/pfbid0T1BsmxWfpEE1oFUqCu4uEmWFRzgJq3hn6BQvCEehmrG9wLHQTU3pLLqhWQN7HakSl) | 2026-11-13T07:57:41+08:00 | completed_no_signal | 200 | 0 | 1 | TSM | 1 | 貼文內容只是預測大盤崩跌且附上TSM股價圖，但沒提及發文者持倉或交易動作，屬於被動觀察或評論，依規則跳過。 |
| [facebook:1711515410333047](https://www.facebook.com/DieWithoutBang/posts/pfbid026b8bNeR6qcGWSBSSCyUysr6UfAmAPDz9wfjbtzjnUMFjsfUNHKbLyNV6jva3d8yYl) | 2026-11-13T09:25:09+08:00 | technical_failure | 200 | — | — |  | 1 | invalid_ticker_format |
| [facebook:1712186250265963](https://www.facebook.com/reel/2160900154802469/) | 2026-11-13T23:21:14+08:00 | pending_confirmation | 200 | 0 | 1 |  | 0 | 內容為抱怨/戲謔遊戲或個人對話，與投資無關且有未分析影片，依規定跳過並標示為需確認 |
| [threads:4029579593664549218](https://www.threads.com/t/Dfr8UpyidFi) | 2026-11-13T23:22:24+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 內容為對話/抱怨遊戲情節或客服式質疑，未提及個人持倉或交易動作，屬於非投資貼文，跳過 |
| [threads:4029622132984581375](https://www.threads.com/t/DfsF_rnmQz_) | 2026-11-14T00:46:53+08:00 | pending_confirmation | 200 | 0 | 1 |  | 0 | 只有籠統悲觀預期（看來準備崩盤了），無明確自我持倉或交易情緒與動作，依規則屬於無法判定投資立場的模糊貼文，跳過 |
| [threads:4029927973335964218](https://www.threads.com/t/DftLiPpGZo6) | 2026-11-14T10:54:32+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 僅為對合約結算的感想/教訓性評論，沒有提及個人持倉或交易情緒與動作，屬於與投資決策無明確關聯的貼文，跳過 |
| [facebook:1713402286811026](https://www.facebook.com/reel/1654964376087063/) | 2026-11-15T00:59:17+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 主要在分享買錶與個人生活風格，影片未分析且無明確投資持倉或情緒表述，屬於與投資無關或模糊貼文，跳過。 |
| [threads:4030353700266598712](https://www.threads.com/t/DfusVYvkmE4) | 2026-11-15T01:00:24+08:00 | completed_no_signal | 200 | 0 | 1 |  | 0 | 生活消費分享（買錶）且影片未分析，內容與投資立場無關，依規則跳過 |
| [threads:4030449832615456486](https://www.threads.com/t/DfvCMS-E67m) | 2026-11-15T04:11:22+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 生活閒聊、談疲累及經營IG，無明確投資立場或持倉動作，屬於非投資貼文需跳過。 |
| [threads:4030642136806956039](https://www.threads.com/t/Dfvt6sNGZwH) | 2026-11-15T10:33:27+08:00 | completed_signal | 200 | 1 | 2 |  | 0 | 對虛擬幣表達強烈負面看法（被騙、失望），情緒偏向痛苦/悲觀但未提及具體交易動作或金額，屬偏多情緒但強度為明顯而非極端。 |
| [threads:4030720656484699170](https://www.threads.com/t/Dfv_xTWmYwi) | 2026-11-15T13:09:27+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 內容為手錶錶帶長度建議，與投資無關，跳過。 |
| [facebook:1714129566738298](https://www.facebook.com/DieWithoutBang/posts/pfbid035itqFRyiCGXafrFUVyhgEFfpybavuQ7gwVEHycxUpFqd4CdJWLwdZZn3CzpG4fj9l) | 2026-11-15T15:30:34+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 生活日常與飲食照片，沒有任何投資情緒或持倉動作，跳過。 |
| [threads:4030791985395698529](https://www.threads.com/t/DfwP_RlAIth) | 2026-11-15T15:31:11+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 生活日常（臉水腫、吃番茄麵）且未提及投資或持倉，跳過。 |
| [facebook:1702487071235881](https://www.facebook.com/DieWithoutBang/posts/pfbid0vzGJfezAr6mDRnz1VmhY5avBR5HhZXiRE5pxW7MrGstFaoUc1upnZZWXG1nD7BFjl) | 2026-11-05T03:04:10+08:00 | pending_confirmation | 200 | 0 | 1 |  | 1 | 貼文內容混合個人自拍與模糊買賣描述，未明確表達持倉情緒或具體投資立場，依規則對此類模糊/無法判定投資相關之貼文跳過。 |
| [facebook:1702731291211459](https://www.facebook.com/DieWithoutBang/posts/pfbid035tHJPGrDoLRNT1A9XfjfBXvDSyrmn5iWmw2KR3FDGtACoaExAgTaYHC8v88ySNUWl) | 2026-11-05T09:23:04+08:00 | completed_signal | 200 | 1 | 2 |  | 1 | 發文者因五月以貸款加碼買進，語氣沮喪無法嘻嘻，顯示被套或重大損失的痛苦情緒，偏多訊號。 |
| [facebook:1702897424528179](https://www.facebook.com/DieWithoutBang/posts/pfbid02FgHSPLV7qxuLxZPP3DLuZoNFMduPa9PpMuQ45gmmdEPFrPfgom5cGkwh8DeLcb1Kl) | 2026-11-05T13:17:14+08:00 | completed_signal | 200 | 1 | 3 |  | 1 | 貼文明確表示當日被套且情緒極度悲傷（被騙、滿手鮮血、哭哭表情），為極端痛苦偏多訊號。 |
| [facebook:1703163464501575](https://www.facebook.com/DieWithoutBang/posts/pfbid02o4AKSbPWCCPWpq62E1UnSNcUdfWCHRfSEAEruZ7RW4fH6sdqB6oXioXAGkmzVnCrl) | 2026-11-05T19:46:58+08:00 | completed_signal | 200 | 1 | 3 |  | 1 | 發文提到貸款買股且目前大幅虧損，附上對帳單顯示總損益-415,390，情緒為痛苦/被套，且有真金白銀持倉截圖強度設為3。 |
| [facebook:1703429887808266](https://www.facebook.com/DieWithoutBang/posts/pfbid0YAJxviLNDv2BGBsdTXgEsHe6YvfRZtgBC3yrc6WksVY3wPGiAc4RsAPYNtx8t1i5l) | 2026-11-06T00:47:04+08:00 | completed_signal | 200 | 1 | 2 |  | 1 | 發文者表示損失20%且情緒崩潰/放棄，為痛苦被套的心態，屬偏多（恐慌）訊號。 |
| [facebook:1703740244443897](https://www.facebook.com/DieWithoutBang/posts/pfbid08wkUP46KGJHSyn1sEhxNV7GG8xZah94T9bVfGe5rfkr9FWtXq4ygRLkYDm9MAqfzl) | 2026-11-06T08:26:00+08:00 | completed_signal | 200 | 1 | 2 |  | 1 | 情緒悲觀、語氣沮喪且暗示大盤重挫與個人難過，屬於痛苦偏多傾向 |
| [facebook:1703792734438648](https://www.facebook.com/DieWithoutBang/posts/pfbid037J5afqWKJv53P9DQt53pwWgXp4e9Lbbwp3fJBQZWf4EPZfakWZGf2GMGHUuEHSdBl) | 2026-11-06T09:40:10+08:00 | completed_signal | 200 | 1 | 3 | 0050.TW | 1 | 發文者以自己的停損換取教訓並請求勿抄底，配合提供委託單截圖顯示已真實停損出場，情緒為痛苦與自責，屬強烈偏多訊號。 |
| [facebook:1704945814323340](https://www.facebook.com/DieWithoutBang/posts/pfbid02SKKe6t1xozYuPPTpT1dezwLh49AYvwJDQgqZpvHNx4eW9m8hhY127syMwEfwgA2Gl) | 2026-11-07T10:23:30+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 商品/服飾推廣貼文，與投資無關，跳過。 |
| [facebook:1705156784302243](https://www.facebook.com/DieWithoutBang/posts/pfbid02HVzyozMABc2YGDoXvrdLj2mb7jaUXuuDMvBGvZyzwFeUVfkkyS3PU1wNRbkDrwg7l) | 2026-11-07T15:09:17+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 生活日常（買陶笛/商品擺拍），與投資無關，跳過。 |
| [facebook:1705237887627466](https://www.facebook.com/DieWithoutBang/posts/pfbid035ydhaSUH8aqj99cm6yxckf9sbjK9Ez8udykEy2RmFBmFAYGpykhp2j2bBTnu8uvHl) | 2026-11-07T17:08:22+08:00 | completed_no_signal | 200 | 0 | 1 |  | 1 | 純遊戲/生活分享，與投資無關，跳過 |
