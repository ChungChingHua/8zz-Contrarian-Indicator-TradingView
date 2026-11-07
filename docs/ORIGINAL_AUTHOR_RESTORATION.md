# 原作者標準還原與單批執行協定

本輪以Fork分支起點 `7b626f2007128eea9cb8111ed4c18185bbfc650a` 的原始檔為依據，不用後來的樣本候選取代標準。原作者hansai-art／Group.G與MPL-2.0保留。

## 不可變來源

- [原README](https://github.com/hansai-art/8zz-Contrarian-Indicator-TradingView/blob/7b626f2007128eea9cb8111ed4c18185bbfc650a/README.md)：恐慌、被套、停損、痛苦偏多；追漲、自大、歡呼偏空；情緒優先於動作。
- [完整_SYSTEM，L159–194](https://github.com/hansai-art/8zz-Contrarian-Indicator-TradingView/blob/7b626f2007128eea9cb8111ed4c18185bbfc650a/scripts/fetch_fb_events.py#L159)：無關類型、否定停損、被動持有、隨便／無想法、粉絲問對帳單與本人曬單區分；強度1輕微、2明顯、3極端；委託證據強制3；ticker不明可空。
- [作者原10組few-shot，L196–217](https://github.com/hansai-art/8zz-Contrarian-Indicator-TradingView/blob/7b626f2007128eea9cb8111ed4c18185bbfc650a/scripts/fetch_fb_events.py#L196)：包含痛苦中買入仍偏多、自信加碼偏空、生活／無想法與粉絲問單排除、委託證據。
- [原執行路徑，L366–439](https://github.com/hansai-art/8zz-Contrarian-Indicator-TradingView/blob/7b626f2007128eea9cb8111ed4c18185bbfc650a/scripts/fetch_fb_events.py#L366)：先AI，AI不可用才keyword；非零direction才產生事件。
- [原強度booster，L317–321](https://github.com/hansai-art/8zz-Contrarian-Indicator-TradingView/blob/7b626f2007128eea9cb8111ed4c18185bbfc650a/scripts/fetch_fb_events.py#L317)：非零方向且委託／成交文字時升為3。

`data/original_author_policy.json` 用AST讀取常數，未執行舊程式；保存原_SYSTEM、全部原few-shot、fallback表、否定前綴、委託片語與來源hash。`original_author.py` 逐字使用原system與範例，僅增加安全傳輸、實際媒體範圍與固定格式／待確認欄位，不增加情緒門檻。

## 撤回項目與保留項目

| 撤回 | 還原後 |
| --- | --- |
| 必須強烈／極度恐慌才偏多 | 依原作者輕微／明顯／極端強度；不以強度3作訊號資格 |
| 原文必須符合PANIC／EUPHORIA regex | AI依完整原文及原few-shot判斷；沒有硬性情緒關鍵字veto |
| 代碼／標的不明、缺逐字ticker證據就阻擋 | 原規則允許確定的yfinance對應，不確定留空；空代碼不阻擋方向 |
| 圖片標的未人工核實就阻擋情緒 | 服務圖像轉錄另標未人工核實，不作情緒額外veto |
| 無關／被動持倉只用縮短版摘要判斷 | 保留原作者完整排除條款、否定句規則與全部範例 |
| 自行以一般無奈／指定強字作後處理再判方向 | 本輪不以舊quality gate重判AI；只保留作者原委託強度booster |

來源與角色註記、金鑰隔離、SSRF／TLS／媒體大小限制、schema／API錯誤檢查仍保留。技術失敗停止，不用keyword生成替代訊號。無關／中性不重送；資訊不足依原規則留待確認，不產生箭頭。先前review-rules與semantic-gate檔案及9篇回應是歷史審查紀錄，不是本輪活躍判讀器，既有已消耗smoke入口不重開。

本輪的AI、後處理、候選Pine全部使用 `original_author.py` 與其hash；worker不呼叫舊`s.classify`、`assess`或`s.generate`。原有history Pine事件一律保留，不追溯重判；多空虧損都計敗的已授權績效修正保留，不還原README舊的不計多頭虧損規則。

## 原始路徑差異與尚無明文邊界

原keyword fallback與AI有差異，例如賣出／停利fallback可能偏多，但AI要求依得意／痛苦情緒；原程式以「AI是否可用」決定路徑，並非兩套同時投票。本輪使用者指定ChatAnywhere且異常停止，因此固定**原AI路徑**，不混入fallback，不自行選對自己有利的結果。

原文同時含「隨便」及其他投資情緒、業配中附本人被套等複合情境，原作者未列所有情況的優先序；保留原prompt完整條款交AI依全文判讀，不另補關鍵字優先順序。若仍無法依原規則判定，輸出pending_confirmation而不是替它補條件。這些邊界不能用後續行情當答案。

## 離線比較

`data/original_policy_comparison.json` 將原作者10組範例答案分別通過舊後處理與原規則後處理，5組箭頭資格不同。這不是新生成，也不是AI準確率；只驗證後加的veto確實改變過作者範例結果。9篇舊回應仍保留，因當時prompt不同，不冒充由原作者prompt重新生成。

## 本輪執行範圍

批次ID：`original-author-20261107-01`，授權最多5次、每篇一次，ChatAnywhere `.tech/v1`、gpt-5-mini／minimal、無重試／付費或官方金鑰備援。規則與計畫hash由workflow及worker雙重確認。

`history_plan.py` 按Asia/Taipei發文時間／key排序；跳過先前測試或處理的11篇，沒有重抓Apify。659篇中648個目前可開始的群組；本批選最早5個。跨平台只有完整原文、引用及媒體身分均一致才合併，短字串不設情緒或長度門檻；文字相同但媒體未證同不誤合併。本批5篇完整原文各不同。尚未驗證同圖的跨平台同文仍分開，不能宣稱全部跨平台重複均已辨識。

影片如實列未分析，使用可見原文與實際靜態圖片，不讀影片／縮圖、不套後加的字數或恐慌門檻。未提供的內容不能補猜。來源ID、原文、時間、網址與媒體hash存於帳本；只有該篇原文、作者判讀提示／範例與實際圖片bytes送給服務，不發送儲存庫檔案、簽名媒體URL、其他秘密或留言。

## 真正遠端帳本與恢復

路徑 `data/history_progress/original-author-20261107-01.json`，存於本PR分支。GitHub contents API以檔案SHA作CAS，HTTPS且不跟隨認證redirect；同一batch concurrency鎖禁止平行執行。GitHub token只用於api.github.com，供應商header僅CHATANYWHERE_API_KEY；無官方key載入或備援。

每篇的狀態轉移：

1. 初始化遠端計畫，not_started。
2. 媒體前檢，保留真實範圍；失敗則input_failure，無生成並停止。
3. **遠端提交unknown＋attempts=1並收到ACK後**才呼叫生成。請求可能送出但未保存，帳本已是unknown，禁止自動重送。
4. 回應安全檢查、原schema驗證／原規則處理；遠端結果提交ACK後才開始下一篇。
5. completed_signal／completed_no_signal／pending_confirmation均不重送；額度、API或格式異常停止。transport不確定留unknown，不以假設未扣點再送。
6. 結果提交失敗時，`.uncommitted.json`僅作人工復原證據；正常帳本本地副本仍維持最後一次ACK狀態，不能將未ACK結果直接畫箭頭。

重複手動啟動只讀同一batch ID：已finished或stopped不再生成；中斷前已保存的結果跳過；若存在unknown整批停等核對。只有最後checkpoint已完成且其餘not_started的乾淨中斷可恢復；不另建ID繞過5次上限。quota未回傳屬未知，不是0點或免費保證；使用者已明確授權此最多5次，無另查未確認餘額接口。

保存服務JSON（安全省略opaque encrypted_content並記完整JSON hash），不宣稱保存原始HTTP位元組；保留全部分類、用量與普通metadata。反射金鑰或疑似key字串不公開；錯誤不記URL／header／raw exception。GitHub與模型憑證不寫進帳本、日誌或artifact。

## 檢查與交付

離線涵蓋成功、失敗、額度不足、重複啟動、stale CAS、送出後中斷、結果提交失敗、已保存結果後恢復，以及未知狀態禁止重送。候選Pine逐筆驗證保留歷史事件、僅加入同規則版本且已遠端保存的非零訊號，待確認／unknown無箭頭。TradingView未實際編譯，不宣稱編譯通過。

本輪完畢後移除自動push啟動，只保留GitHub Actions手動入口及已消耗batch ID的防重送保護；一般pause、持續排程、Pages仍關閉，不合併PR。

## 已確認的媒體環境限制與零生成恢復

首段在第一篇媒體前檢停止，遠端帳本證明generation attempts=0。無金鑰診斷顯示CDN僅解析IPv6，runner回errno101（network unreachable）；公開A記錄查詢也無IPv4，公開照片頁只回登入頁，沒有可用圖片中繼資料。不改寫CDN主機、不關TLS、不建立網路隧道，也不要求Facebook登入憑證。

對這個已確認的network-unreachable條件，保留圖片未分析／錯誤代碼，允許僅依可見原文繼續；不是假裝OCR或取縮圖。若缺圖導致原作者規則無法判斷，就pending_confirmation。TLS、SSRF、格式等其他安全失敗不被此分支忽略。這是來源範圍如實揭露，不是新增或刪除情緒條件；原system／few-shot／規則hash不變。

一次性operator恢復只接受「同一batch、遠端0次生成、所有attempts=0、唯一停止原因為media preflight、沒有任何HTTP回應」；保存先前input_failure歷史後恢復not_started。若已有任何生成／unknown／quota錯誤則拒絕，不能用此開關繞過上限或重試。122項離線測試通過，包含此範圍及安全錯誤不被忽略。

## 首筆HTTP200的離線重驗：修正過嚴媒體註記檢查

首筆唯一生成回傳HTTP200、strict JSON有效、gpt-5-mini／minimal及完整原五欄，direction=-1／strength=2。模型另列「圖片未提供、readable=false、visible_text空」的誠實未分析註記；舊本地檢查只比圖片數量而拒絕，造成image_coverage_mismatch，並非服務schema或額度異常。

已離線重驗保存回應，不重送：只有images_supplied=0、索引確在已聲明未分析圖片、readable=false且visible_text為空時，才將該筆移為unanalysed_image_notes，實際images仍為空。若聲稱看過未提供圖片或虛構可讀文字，仍拒絕。原回應JSON／hash不變，舊錯誤另存local_validation_history，原作者direction／strength不更改。

專用operator校正只接受此確切HTTP200本地檢查失敗、已預留1次且其餘4篇從未嘗試的狀態；遠端保存校正後才續未開始4篇，不重送第一篇，總上限5不重設。若quota顯示0仍停止。原system／few-shot／hash不變；這是技術檢查修正，不能把它當額外情緒veto。離線測試124項通過，逐筆原回應安全保存方式不變。

## 完成結果與非情緒資料校正

本批5次生成均取得HTTP200有效JSON；有訊號2、無訊號2、待確認1、目前技術失敗0、unknown0，剩餘未開始自動候選643群組（先前11篇測試／處理不在隊列）。2張圖未讀、1張實際附圖、1篇影片未分析均明列，未以缺圖或缺碼額外阻擋可判定情緒。

第2筆6505.TWO依證交所靜態發行人／市場資料校正為6505.TW，上市日期2003-12-26早於主貼文。這是yfinance標的格式校正，不使用後續行情，不改direction／strength，不作訊號veto；原模型值及參照hash保留。另記AI原強度與原委託booster實際命中情況，避免將AI敘述誤稱已確認成交。125項離線測試通過。

實際結果／使用步驟見[本批報告](HISTORY_BATCH_01_RESULTS.md)。臨時push啟動已移除，只保留固定batch的手動復核／受限恢復，授權5次耗盡後不再生成。持續排程、Pages、合併仍關閉。候選Pine未經TradingView實際編譯。
