# 2026/11/14 歷史續跑紀錄

**尚未全部補齊：剩10篇Facebook圖片無法讀取，沒有生成或冒充完成。** AI額度已可使用，本輪沒有因AI額度停止。

## 本次成果與統計口徑

- 三段執行合計64次生成HTTP請求，皆HTTP200；61筆通過既有驗證，3筆ticker字串不符合本地格式驗證。原始回應保留，沒有重送。
- 新增18筆事件、32篇無訊號、11篇待確認；3筆技術失敗未寫訊號。跨平台貼文數不等於事件數。
- 完整指標及策略均為 **380事件＝原歷史151＋累計新增229**。原作者情緒標準、同棒最後發文、大台70萬本金／開倉門檻、1口每點200、單邊費用250、ATR／移動停損都保留。
- 資料抓取截止仍為台灣時間 **2026/11/7 20:15:59**，666篇；未擴大至11/14或重抓整段歷史。
- 連續已走訪前綴為 **11/5 01:23:43**（包含較早待確認與失敗，不是全數成功）；最早未處理缺口為 **11/5 03:04:10**。
- 另外已處理可讀資料至最後保存貼文 **11/7 17:09:34**，不能用這個日期掩蓋較早缺口。
- 最新事件為 **11/7 00:54:48**；它不代表資料處理完成日期。
- 全部貼文狀態：有訊號231、無訊號306、待確認99、技術失敗13、媒體輸入失敗7、狀態不明0、尚未處理10。舊樣本／待確認／失敗完整保留於[未完成清單](../data/history_unresolved_20261114.json)，沒有自動轉成完成。
- 本輪逐篇摘要、來源、理由、圖片／影片範圍及token用量見[機器可讀紀錄](../data/history_resume_20261114.json)；原文／原始模型JSON與processed分開保存於history_progress，來源檔沒有改寫。

## 費用、模型及真正阻塞

請求設定：ChatAnywhere .tech/v1、gpt-5-mini／minimal。服務回傳名稱為gpt-5-mini、reasoning.effort為minimal；**僅供應商回傳／宣稱，未獨立驗證底層模型或實際推理**。

API回報輸入185833、輸出10020、合計195853 tokens，reasoning_tokens回報0。實際免費點數扣除／剩餘請求額度未取得，點數不等於tokens，也沒有宣稱零扣點。模型清單查詢0、其他AI供應商查詢0。64篇請求共附入40張圖片；10筆影片附件未分析，文字獨立分析者如實保留範圍，未用縮圖冒充影片。

本輪Apify共4次新run，每次請求maxTotalChargeUsd仍0.10：
| run ID | 平台／狀態 | 實際build | API usageTotalUsd |
|---|---|---|---|
| T5aL34lZ0cAhRu17S | Threads／SUCCEEDED | 0.1.72 | US$0.080 |
| i22Es0nKg6gd7bpEZ | Facebook／SUCCEEDED | 0.0.421 | US$0.061 |
| aN1ESUqN4kVceCqBH | Facebook／ABORTED、dataset0篇 | 0.0.421 | US$0.001 |
| fPBlsZbRm65xzhyGX | Threads／SUCCEEDED、僅2篇 | 0.1.72 | US$0.030 |

合計 **US$0.172**，只加每run的usageTotalUsd一次，不再疊加事件費或usageUsd；這是API觀察，不是獨立結算帳單。月啟動預留由61至65／70，沒有提高上限或儲值。Apify API GET53、POST5（啟動4、中止1）；GitHub與公開圖片下載HTTP另計，不把這些數字當成全部網路流量。

第三個run回報上限0.057529，程式原本要求必須精確等於0.10而誤中止；這是本地檢查錯誤，不是AI限額。已改為「服務確認使用者上限、數值有限且正數、且不超0.10」，並補3項離線回歸；缺失、未確認、NaN／Infinity、零、負數或超額仍拒絕。中止run確認dataset0篇、未生成AI，已保存且未重開。

Apify帳號API在2026-11-14T07:22:09.580563+00:00回報月用量上限US$5、已用4.978514389197657，差額 **US$0.021485610802343**。這是帳號整體「用量上限減已用」推算差額，不是現金餘額，也不是本專案獨自用了整個金額。剩10篇需要重新取得不可讀媒體，現有差額無法可靠補齊，故保存停止。

核對全部媒體更新run：17個run、171個預留貼文key，重複預留0（包含已中止0資料的run，不宣稱這些key全都抓取成功）。已完成AI與已有圖片不重送。剩餘10篇均屬已中止批次；未自動重開。

## 十篇缺漏

| 台灣發文時間 | 貼文ID | 原圖片檢查結果 |
|---|---|---|
| 2026-11-05T03:04:10+08:00 | [1702487071235881](https://www.facebook.com/DieWithoutBang/posts/pfbid0vzGJfezAr6mDRnz1VmhY5avBR5HhZXiRE5pxW7MrGstFaoUc1upnZZWXG1nD7BFjl) | media_http_status_rejected |
| 2026-11-05T09:23:04+08:00 | [1702731291211459](https://www.facebook.com/DieWithoutBang/posts/pfbid035tHJPGrDoLRNT1A9XfjfBXvDSyrmn5iWmw2KR3FDGtACoaExAgTaYHC8v88ySNUWl) | media_http_status_rejected |
| 2026-11-05T13:17:14+08:00 | [1702897424528179](https://www.facebook.com/DieWithoutBang/posts/pfbid02FgHSPLV7qxuLxZPP3DLuZoNFMduPa9PpMuQ45gmmdEPFrPfgom5cGkwh8DeLcb1Kl) | media_http_status_rejected |
| 2026-11-05T19:46:58+08:00 | [1703163464501575](https://www.facebook.com/DieWithoutBang/posts/pfbid02o4AKSbPWCCPWpq62E1UnSNcUdfWCHRfSEAEruZ7RW4fH6sdqB6oXioXAGkmzVnCrl) | media_http_status_rejected |
| 2026-11-06T00:47:04+08:00 | [1703429887808266](https://www.facebook.com/DieWithoutBang/posts/pfbid0YAJxviLNDv2BGBsdTXgEsHe6YvfRZtgBC3yrc6WksVY3wPGiAc4RsAPYNtx8t1i5l) | media_http_status_rejected |
| 2026-11-06T08:26:00+08:00 | [1703740244443897](https://www.facebook.com/DieWithoutBang/posts/pfbid08wkUP46KGJHSyn1sEhxNV7GG8xZah94T9bVfGe5rfkr9FWtXq4ygRLkYDm9MAqfzl) | media_http_status_rejected |
| 2026-11-06T09:40:10+08:00 | [1703792734438648](https://www.facebook.com/DieWithoutBang/posts/pfbid037J5afqWKJv53P9DQt53pwWgXp4e9Lbbwp3fJBQZWf4EPZfakWZGf2GMGHUuEHSdBl) | required_refreshed_images_unavailable |
| 2026-11-07T10:23:30+08:00 | [1704945814323340](https://www.facebook.com/DieWithoutBang/posts/pfbid02SKKe6t1xozYuPPTpT1dezwLh49AYvwJDQgqZpvHNx4eW9m8hhY127syMwEfwgA2Gl) | media_http_status_rejected |
| 2026-11-07T15:09:17+08:00 | [1705156784302243](https://www.facebook.com/DieWithoutBang/posts/pfbid02HVzyozMABc2YGDoXvrdLj2mb7jaUXuuDMvBGvZyzwFeUVfkkyS3PU1wNRbkDrwg7l) | media_http_status_rejected |
| 2026-11-07T17:08:22+08:00 | [1705237887627466](https://www.facebook.com/DieWithoutBang/posts/pfbid035ydhaSUH8aqj99cm6yxckf9sbjK9Ez8udykEy2RmFBmFAYGpykhp2j2bBTnu8uvHl) | media_http_status_rejected |

全部尚未生成，原文保留；沒有以文字假裝已看圖。這10篇以及既有99待確認／20失敗都列在未完成清單，不能宣稱已全部判讀完成。3筆本輪格式失敗為facebook:1700739848077270、facebook:1700801464737775、threads:4023406251229152584，均HTTP200但ticker格式不合，沒有重新付費問模型。

## 接續及驗證

先取得這10篇缺失圖片，或等待Apify可用額度足夠；後續只針對缺漏處理，不重抓整段、不重送已成功／待確認／技術失敗或狀態不明項目。中止run的0筆dataset與原始錯誤已有證據，後續須核對這個明確紀錄再處理，不能把未知請求當作未送出。

最新快取artifact為 **history-media-cache-20261114-last-threads**，run **43570686068**、id **14103938782**，到期 **2026-11-28T07:22:33Z**；本次用過的圖片仍留在舊來源artifact可追溯，但剩10篇目前沒有可用快取。不得因artifact到期就默默重抓已完成資料。

252項離線測試及成對Pine確定性檢查通過。最新兩份[完整指標](../candidates/8zz-history-latest.pine)／[完整策略](../candidates/8zz-strategy-latest.pine)保留相同380五欄事件；**尚未在TradingView實際編譯**。策略預設回測截止仍11/6；11/7週末事件保留在資料，若要觀察其在下一交易日的策略行為，需自行調整截止日期並載入相應行情，不能把沒有日盤棒當漏資料。

所有本輪一次性入口已停用；沒有啟用持續排程、發Telegram、發布網站或合併PR。GitHub不會自動同步TradingView，更新時請分別完整取代兩份Pine。

官方唯讀用量欄位依據：[Get user's limits](https://docs.apify.com/api/v2/users-me-limits-get)。run費用與cap證據見[預算稽核](../data/history_media_repairs/budget-audit-20261114.json)及[最後用量](../data/history_media_repairs/final-budget-20261114.json)。
