# 2026/11/11 歷史圖片修復與續跑結果

本次先修復圖片來源，再恢復能證明零生成的三篇，接續其餘未判讀歷史；沒有重新抓取整段歷史、重送既有 AI 回應、改原作者情緒規則、啟用排程、通知、部署網站或合併 PR。

## 結果與完成範圍

- 原因修復：三篇指定貼文以原 Actor 重新取得媒體；ID、作者、原文、時間與附件路徑識別一致，三張圖均 HTTP 200。先存內容 hash 與檔案快取，再送模型；先前的一篇成功待確認回應未重送。
- 本階段 100 次生成＝99 次 HTTP 200、1 次 HTTP 429，無自動重試。99 筆成功回應通過固定格式／一致性驗證，其中47有訊號、46無訊號、6待確認；另有3篇新的媒體輸入失敗，生成次數為0。
- 完整候選 **341事件＝151原歷史＋190累計新增**，相較本階段前294新增47。方向／強度沿用政策 SHA256 `8ccd8bbe6388705261e7240897417683f2dc6e2016f5db9d5eca462533837162`。
- 最後成功回應對應 **2026/10/12 00:00:20** 貼文；**10/12 08:44:32** 貼文因429保留技術失敗；下一篇未開始 **10/12 09:15:16**。最新事件為 **10/10 02:44:02**。以上均 Asia/Taipei，訊號日期不代表資料完成日期。
- 全666來源貼文：有訊號192、無訊號237、待確認77、技術失敗9、輸入失敗4、狀態不明0、尚未開始147。來源貼文數、生成群組數與Pine事件數分開計算。
- 資料抓取截止仍為 **2026/11/7 20:15:59.578797**；尚未宣稱全部判讀補齊。
- 原生策略／網站維持9/30展示截止，策略候選313事件；完整歷史指標341事件包含10月結果。沒有擴大展示範圍或改變策略成交引擎。

## 圖片快取與恢復

原始圖片 URL 短效／CDN不可達已在前次診斷確認。這次只向既有兩個 Actor 提交必要的指定貼文 URL：Facebook用 startUrls、Threads用 urls／postUrls，均為官方文件支援模式。未向它們要求整段頁面歷史。

最初兩次run驗證三篇；後續按需要以每批最多12個指定網址刷新。每次US$0.10、timeout180、memory512、maxItems50、restartOnError=false；實際Facebook最低執行記憶體由平台回傳1024MB。主貼文、作者、時間及媒體識別仍逐筆驗證，不把其他作者／回覆／轉貼或變動內容混入正式archive。

圖片每檔最多8MB、整體快取上限128MiB，沿用公網IP／網域／TLS／無重新導向限制。快取讀取前核對SHA256、MIME、格式magic、大小與路徑；任何不符均不送AI。影片保持「未分析」，不以縮圖代替。

三篇先前失敗僅因attempts=0、無HTTP／原始AI回應且媒體實測可讀才恢復。舊錯誤保留在每筆input_failure_history，之後各只生成一次；有模型回應／待確認／未知者不自動重送。

本輪77張圖片實際附入68次請求；讀取快取或下載成功不是模型已完成圖片判讀的證據，結果仍按每篇HTTP與格式驗證紀錄。未宣稱人工核圖。

受控快取：
- 工作流程 run：`43021582706`
- Artifact：`history-media-cache-20261111-continuation`，ID `13856592316`
- 壓縮大小52,131,162 bytes，保留至2026/11/25 20:58:24（台灣時間）。
- 內容是圖片bytes與去除signed query的manifest，不含API金鑰或原始signed URL。下一次續跑應下載這份新快取，先驗hash，再從遠端帳本的未送出位置接續；不用再次抓已快取的圖片。
- 保留的原始模型回應、處理後結果、來源、規則版本與圖片SHA均可追溯。

## 實際可取得用量與費用

服務回報gpt-5-mini／minimal，僅服務宣稱，不是底層模型獨立驗證。輸入289431／輸出16958／合計306389 tokens。服務回覆當前24小時跨免費模型共用100次額度用盡；實際扣點、剩餘點數及重設時刻未知，沒有將tokens換成點數或宣稱零扣費。最後429未回報usage，以上tokens只加總有回報的99筆，不能推定失敗請求零tokens或零扣點。先前已成功的一次請求保留未重送。

Apify本階段9次啟動＝初始修復驗證2＋續跑7，API最新run費用合計 **US$0.520**（Facebook0.250、Threads0.270）。這是各run的usageTotalUsd加總，沒有重複加usageUsd或計費事件；非已核對最終帳單，仍可能延遲更新。各run均完成，未提高單次上限或儲值。共用月計數 **48→57／70**，尚餘13次保護額度。

| 平台 | 實際版本 | run ID | 狀態 | API usageTotalUsd |
|---|---|---|---|---:|
| facebook | 0.0.416 | `9Ese4DLwPHsgVPn46` | SUCCEEDED | 0.006 |
| threads | 0.1.70 | `cpP8JIHtvctY2cOJ3` | SUCCEEDED | 0.03 |
| facebook | 0.0.416 | `Rrgbhmob2fwP8Hy8k` | SUCCEEDED | 0.061 |
| threads | 0.1.70 | `RsGX7akhZCyEo6Nem` | SUCCEEDED | 0.08 |
| facebook | 0.0.416 | `sfTEBbx4xdszoRE42` | SUCCEEDED | 0.061 |
| threads | 0.1.70 | `bzUVWdIk2BknUi8CM` | SUCCEEDED | 0.08 |
| facebook | 0.0.416 | `wYEIM1iuL5stQ3S1x` | SUCCEEDED | 0.061 |
| threads | 0.1.70 | `cu9xU76Kw4SJto3Pb` | SUCCEEDED | 0.08 |
| facebook | 0.0.416 | `bvjp4TpwMPdRByGbe` | SUCCEEDED | 0.061 |

Apify HTTP合計GET140／POST9（初始GET13／POST2、續跑GET127／POST7）；模型生成100次另列，圖片下載與GitHub進度保存另計，不宣稱這是全部HTTP流量。

## 失敗與後處理

三篇新的輸入失敗仍保留，不產生箭頭或自動重送：
- `facebook:1663843951766860`：圖片未能完整取得。
- `facebook:1671838414300747`：原紀錄IndexError。離線檢查發現可重現的相簿索引問題：同一失敗物件同時出現在兩個scope清單時，舊程式重複轉換索引；已修正為每個物件只轉一次並加回歸。原失敗未改成完成，也沒有為它新增生成。
- `facebook:1677083933776195`：含未支援或不明媒體格式，保留輸入失敗。

另核對兩筆模型代碼候選：天元→4164.TWO、環球晶→6285.TW缺乏支持／與官方公司代碼資料不符，僅將輸出ticker清空；不猜替代持倉，也不改方向、強度或事件數。原raw_response及原processed另保留，並附ticker_reconciliation；圖片轉錄仍標示未經人工核實。
- [TPEx：4164承業醫](https://ic.tpex.org.tw/company_chain.php?stk_code=4164)
- [TWSE：6285啟碁](https://www.twse.com.tw/pdf/ch/6285_ch.pdf)
- [TPEx：6488環球晶](https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&o=htm)

恢復3篇零生成失敗會讓input_failure的原始狀態差額減3，因此報告另保留status_count_transitions，status_counts則加回恢復數、呈現本階段實際新增的3篇輸入失敗；沒有用負數失敗掩蓋問題。

## 檢查與接續

原歷史151事件保留、陣列配對／排序／方向強度檢查通過。完整指標18個初始化函式、各最多20事件；策略16個函式。新增的快取、路徑、身分、額度、無重試、恢復計數與相簿索引回歸均為離線技術檢查，沒有增加AI品質樣本或情緒條件。新版未經TradingView實際編譯或策略成交驗證。

本次因實際429停止，兩個一次性入口完成後停用，進度、費用與快取位置封存。額度恢復後只續未送出項目，已有回應不重問；資料不足／失敗／未知保留明細，不宣稱已補齊。

- [完整歷史指標Pine](../candidates/8zz-history-latest.pine)
- [9月底範圍的原生策略Pine](../candidates/8zz-strategy-latest.pine)
- [來源貼文狀態清單](../data/history_completion_inventory.json)
- [最初三篇修復帳本](../data/history_media_repairs/media-repair-20261111-01.json)
- [續跑媒體帳本](../data/history_media_repairs/20261111-media-repair-01.json)

TradingView需下載全文、在Pine Editor整份取代、儲存並更新圖表；GitHub更新不會自動同步。
