# ChatAnywhere 與 PR #1 資安審查

審查日期：2026-11-07（Asia/Taipei）。範圍：公開文件、公開 Git 原始碼、PR #1 程式碼、無憑證 HTTPS HEAD。未使用 AI／ChatAnywhere／Apify 金鑰，未查帳號模型，未傳貼文／圖片，未執行生成、付費請求、侵入掃描或供應商範例。GitHub 連接器僅用於授權範圍內的原始碼讀取與 PR 修改。

**結論：修正後可試用，但只限經人工去識別、確認有處理依據的小量公開文字／裁切圖片；目前不建議把整批原始公開貼文與完整圖片直接送入此服務。線上功能仍停用，本報告不構成解除暫停的授權。** 公開不等於沒有隱私、著作權或存取憑證風險，也不代表可任意交由更多第三方保存。

本地程式風險原為高；已修正項目降低了憑證外洩、SSRF 與自動發布風險。供應商保存、次處理者及真實模型的透明度仍有中高風險，不能靠修 PR 解決。

## 證據與審查邊界

- [S1 公開儲存庫](https://github.com/chatanywhere/GPT_API_free)，本次樹狀查詢 ref main 回傳 SHA `f4e4054594ec4998886e2bb7ae7650e22356d641`、truncated=false。[API 樹狀證據](https://api.github.com/repos/chatanywhere/GPT_API_free/git/trees/main?recursive=1)。ref 可變，本報告保存當時 SHA／清單摘要，不能把日後 main 當同一版本。
- [S2 README](https://github.com/chatanywhere/GPT_API_free/blob/main/README.md)、[LICENSE](https://github.com/chatanywhere/GPT_API_free/blob/main/LICENSE)。MIT 標示權利人「牛爷爷信息技术（南京）有限公司」，這不是對其登記、實際營運主體或服務安全的獨立查證。
- [S3 隱私政策](https://chatanywhere.apifox.cn/doc-8793261)，主要檢視 §3.3–3.4、§5、§7、§9。
- [S4 服務條款](https://chatanywhere.apifox.cn/doc-8793258)，主要檢視 §4、§7–9、§13–17；[操作文件](https://docs.chatanywhere.tech/)包含路由分組說明。
- [S5 GitHub OAuth 官方說明](https://docs.github.com/en/apps/oauth-apps/using-oauth-apps/authorizing-oauth-apps)。這說明 scope 的意義，**不是** ChatAnywhere 實際要求的 scope 證據。
- [S6 PR #1](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/pull/1)。本輪審查前 head：`51e27179cc4fa3447ce9e011c2e7d194ad5a9520`；[原圖片下載／輸出程式](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/blob/51e27179cc4fa3447ce9e011c2e7d194ad5a9520/scripts/social_pipeline.py)、[原工作流程](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/blob/51e27179cc4fa3447ce9e011c2e7d194ad5a9520/.github/workflows/fetch-fb-events.yml)。修正見同 PR 最新 diff。

## 服務實際公開了什麼

S1 的完整樹狀清單只有 README、MIT LICENSE、Git 設定、Issue 範本、圖片及 **8 個 demo Python 檔**：語音、轉錄、聊天、圖片輸入／生成與 Responses 範例。檢視的聊天與 Responses 範例都是 `OpenAI(..., base_url=...)` 客戶端呼叫；Responses 範例另示範 web search／function calling。沒有發現服務端路由、認證、金鑰儲存、日誌、帳務、租戶隔離或刪除實作。

所以能獨立確認的是「這個 repo 沒有公開可供本次審查的服務端實作」。不能推論業者所有其他程式都未開源，更不能把 demo 的 MIT 授權視為託管服務的無條件商用授權。未執行任何 demo；其硬編碼金鑰佔位符、列印完整回應／錯誤的寫法不適合直接照搬到正式流程。

## 業者自稱與可驗證證據

| 項目 | 業者公開說法 | 本次能驗證／不能驗證 |
|---|---|---|
| 資料保存 | README 用語絕對；正式政策有保存例外 | **確認文件用語不一致**。不能以 README 保證零保存、不能保證刪除完成 |
| 個資與第三方 | 正式政策允許必要技術紀錄與第三方處理，並將資料責任交給使用者 | 未取得涵蓋實際通道的完整次處理者、地區、保留時限與刪除證明 |
| 刪除 | 政策允許申請刪除，但有法令／安全／爭議等例外 | 未登入、未提交刪除申請；沒有端到端刪除時限或技術驗證 |
| 真實模型 | 服務宣稱轉發／路由上游模型 | 回應 model、reasoning、usage 都可由代理產生；不能證明後端權重、版本或推理強度 |
| 服務穩定 | 有狀態頁；條款不承諾特定可用性 | 狀態頁不是獨立 SLA；本輪無負載／生成測試，先前官方 OpenAI 的 429 不能用來評價 ChatAnywhere |

S3 的精確含義是：必要使用紀錄可能保留，內容也有安全、排障、爭議、法令等例外；沒有給出所有資料的固定最長期限。可要求刪除不等於保證所有備份與第三方同步清除。`store=false` 只是請求參數，不能限制代理／上游的實際保存行為。

## 風險、影響與處置

| 等級 | 已確認問題／殘餘風險 | 影響 | 修正或試用前條件 | 證據 |
|---|---|---|---|---|
| 高 | 服務端與完整資料處理鏈不可審查 | 無法證實保密、隔離、刪除與上游身分 | 不傳客戶資料、登入截圖、帳戶／委託編號、私密內容；索取書面保存與次處理者說明 | S1、S3、S4 |
| 高 | 公開貼文圖片仍可能含臉、姓名、帳戶持倉與他人個資 | 擴大第三方處理與保存範圍 | 人工去識別、裁切；公開可見不代表授權充分；目前沒有自動個資辨識保證 | S3 §2、S4 §7、S6 |
| 高，已補強 | 原圖片下載只驗主機字尾，會跟隨 redirect，未綁定 DNS 檢查結果 | 可被誘導連內網、metadata 位址或非預期站點；URL／流量外洩 | 新下載器拒絕轉址、userinfo／非 443、非公開 IP；實際連線固定已檢查 IP、以原 hostname 驗 TLS；代理環境不繞過、直接留待確認 | S6；scripts/safe_media.py |
| 高，當前檔已移除、歷史未清 | 原 archive 的結構化 URL 有簽名查詢參數，且原 workflow 會 commit／上傳整包 JSON | 即使非 AI 金鑰，持有媒體簽名網址可能取得內容 | 最新公開 JSON 移除 URL 簽名參數，未修改原貼文文字；原始上傳檔留在 Git 外。**舊 Git／既有 artifacts 仍可能保留，需要另做清理／撤銷或等待到期** | S6 data/social_posts.json、原 workflow |
| 中高，已暫停 | 原更新 job 有 contents:write，並在失敗時提交資料 | 不可信資料或程式／依賴被污染時可持續發布 | 現在 job 僅 contents:read、無 Secret、無 checkout 或發布，Python 預設暫停；未自動刪歷史、未合併 | S6 workflow、data/online_paused.json |
| 中，已補強 | 原圖片僅信 Content-Type | HTML 偽裝、超大／慢速資料與錯誤格式 | 上限 4 張、每張 8MB，讀取大小及宣告長度檢查，JPEG／PNG／WebP magic 配對，10 秒 socket／30 秒關閉計時器；**magic 不是完整解碼驗證或去識別** | safe_media.py、test_security.py |
| 中，已限制能力 | 貼文與圖片提示注入仍可污染分類 | 錯誤方向、理由或標的，影響研究結果 | 不提供 tools、檔案／環境存取或命令執行能力；只接受固定 schema，拒絕工具輸出；字串與 enum 驗證、Pine escaping；仍須人工複核，不能把 schema 正確當語意正確 | social_pipeline.py、update_pine_script.py |
| 中，部分修正 | 供應鏈含 mutable Action tags、前端 CDN 與第三方統計 | 改版／供應鏈污染、瀏覽資料外送 | Actions 改釘完整 SHA、checkout 不持久保存 Git 憑證；圖表 CDN 加 SRI、移除訪客統計。Python 行情依賴雖固定版本但無完整 hash lock／SBOM；Actions、函式庫未逐行全面審計 | .github/workflows、requirements.txt、docs/index.html |
| 中，已補強 | 原網址欄位 escaping 但不檢查 URL scheme，回應 usage／metadata 過度信任 | 點擊式不安全 URL、污染公開資料 | 來源只允許 HTTPS Meta 網域，前端拒絕非預期 scheme／host；公開結構 URL 去查詢參數，輸出長度限制，usage 僅保留定義的非負整數，provider 回應若反射當次金鑰則拒絕持久化 | public_safety.py、social_pipeline.py、docs/index.html |
| 中，新增使用者證據 | 使用者回報授權畫面僅要求 Email addresses 與 Profile information 讀取，未列 repository／workflow；權杖保存仍未知 | 可能擴大 GitHub 帳號存取權 | 初次審查只讀登入 HTML；後續使用者提供畫面描述為 Email addresses／Profile information 唯讀，未列 repository／workflow，本輪未獨立復核。權杖保存方式仍未知；日後若出現額外權限先釐清，不為領免費 key 給不必要權限；可至 GitHub Applications 檢查／撤銷 | S2、S5、https://chatanywhere.tech/ |
| 中／用途待確認 | 免費版限個人非商用／教育／非營利科研 | 自用獲利交易或公開產品可能有條款邊界 | 個人離線研究較接近允許場景，但不能自行確定獲利交易屬非商用；必要時請業者書面確認。**不延伸認定可用於客戶、顧問、收費訊號或商業 SaaS** | S2、S4 |

## 網域、TLS 與金鑰傳送

官方文件列 `api.chatanywhere.tech`／`api.chatanywhere.org`；PR 固定 `.org/v1`，不接受任意 base URL，兩個 provider 分別讀 `CHATANYWHERE_API_KEY`／`OPENAI_API_KEY`，不互相代用。本次暫停後兩者均不注入 workflow，也不讀取金鑰。先前程式的 Bearer Header 不放進 URL；帶認證請求拒絕 HTTP redirect，已保留測試。這是可審查的本地隔離，不能保證使用者從未將錯誤金鑰貼進錯誤 Secret。

本次只對兩個 API **根目錄**各做一次無認證 HEAD，未送任何 Authorization／API 內容，未跟隨轉址。均觀察到 HTTP 302 → `https://chatanywhere.tech`。這不能證明 `/v1/models` 或 `/v1/responses` 有相同行為，亦未測認證後行為。

連線經本環境受管代理，TLS hostname 驗證通過、使用 TLS 1.3；但憑證簽發者是本地 TLS 檢查代理所顯示的 OpenAI, LLC，**不是對 ChatAnywhere 與 OpenAI 有關係的證據**。未取得可獨立確認的原站憑證鏈、CA、有效期或端到端 TLS，因此不列原站憑證「已驗證」。沒有關閉 TLS 驗證，也沒有繞過代理以取得更好看的結果。

公開登入頁是前端殼，未取得實際 OAuth consent 的權限清單；不把「綁定 GitHub」等同僅讀基本資料。沒有執行其 JS 或任何供應商 demo。

## 本地模型能力邊界與仍不能保證的事

模型收到的是選定原文、最小化的引用文字與實際圖片 bytes；不把 API key、工作目錄、Git 憑證、環境變數或下載 URL 放進 prompt。API Header 的第三方 key 仍由代理業者看得到。程式沒有回應到工具／shell 的執行循環，模型不選本地檔案路徑；產出檔案由固定本地程式寫入，不由貼文決定。

只有 prompt 指示忽略注入並不夠；已用無工具權限、回應型別與字串限制隔離能力，但無法離線證明模型不會誤判。惡意圖片文字仍可讓模型輸出看似合法的錯誤分類。不得把分類輸出直接當作自動交易授權。本專案目前沒有加入下單能力。

原始公開貼文、ID、附圖中的個資及歷史記錄不會因簽名去除自動匿名化。`public_safe` 刻意保留原文，並非通用 DLP／秘密偵測器；如果原文自己含金鑰或私密截圖，仍需人工隔離。舊 commit、fork、下載快取與 artifact 無法保證回收，本次未做破壞性 history rewrite 或刪除外部產物。

## 驗證與後續條件

- 47 項離線測試通過、Python 編譯通過；新增測試涵蓋暫停先於金鑰讀取、混合公私 IP／metadata IP 拒絕、IP pinning 與 TLS hostname、轉址拒絕、HTML／超大圖片、檔頭驗證、簽名移除、工具輸出拒絕、工作流程無 Secret／寫入權限。
- 所有網路處理測試使用本地 mock；只讀 HEAD 與公開文件存取和這些離線測試分開，沒有使用真實 API key、生成或傳送貼文／圖片。
- 此輪字面金鑰樣式檢查未發現目前文字檔含長 `sk-...` 常值；這不是完整秘密掃描、所有歷史 commit／log／artifact 的無洩漏證明。
- 暫停開關預設 fail closed：檔案不存在、未明確設 false 都不允許模型查詢／內容傳送；workflow 為無憑證暫停 stub，Pages 部署 job 也停用。修改開關／恢復工作流程需要新的明確授權，**本報告不恢復服務**。
- 若未來要試用，先完成資料去識別及授權／用途確認、歷史敏感網址處置與供應商資料處理條件核對，再另行授權小量測試。若要求可證明零保存、真實模型或客戶／商用資料保密，現有證據不足，**不建議此免費代理作為處理管道**。

## 後續補充：使用者提供的 OAuth 授權畫面證據與一次性授權

2026-11-07，使用者於本對話提供實際看到的授權畫面描述：Email addresses（read-only）、Profile information（read-only），未列出 repository 或 workflow 權限。這是**使用者提供的授權畫面證據**，本輪沒有獨立登入或復核原始畫面，不反推精確 OAuth scope 代碼，也不推論所有歷史權杖權限。權杖保存、刪除、租戶隔離與後端使用方式仍未驗證。

使用者另明確授權一次技術評估：僅固定 Facebook／Threads 各一篇公開貼文及圖片，CHATANYWHERE_API_KEY 獨立注入；模型查詢最多一次、生成最多兩次且無自動重試。必要功能不支援或第一筆失敗即停止，不換模型、供應商或降級格式／圖片。一般暫停開關保持 true，獨立一次性流程僅在記憶體中開放固定樣本所需路徑，完成後停止；不改 archive、Pine、不啟用 schedule／Pages、不合併。這不代表確認免費版適合個人交易研究，亦不適用客戶或商業服務。

圖片來源從既有歷史 archive 在 runner 本地讀取，只有指定兩筆的原文與圖片 bytes 會送到供應商；不把儲存庫檔案或原始帶簽名網址送入模型，也不將這些網址重新寫回公開資料。產物僅為去除敏感資料的專用 audit。免費點數查詢若沒有已確認的接口／回傳欄位，明示未知，不能以 token 用量推算點數或宣稱零扣點。

## 本次有限授權實際結果（已停止）

[一次性 Actions 執行紀錄](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42347578466)。模型清單 GET /v1/models 收到 HTTP 403，沒有可安全辨識的錯誤代碼或額度欄位，不能判定拒絕來自服務或中介層，也不推定是金鑰無效、餘額不足或模型不支援。依指示立即停止、無自動重試。

模型查詢 1 次、生成 0 次、其他供應商查詢 0 次、圖片下載 HTTP 0 次。這些是供應商／媒體請求計數，不包含 Actions 自身的 checkout、log／artifact 上傳；獨立審查檔案保存另使用 GitHub contents GET 1 次及 PUT 1 次。一般暫停旗標一直保持 true，原 659 篇資料與 Pine 沒有改動。一次性入口現已停用，不使用任何 Secret；PR 及 Pages／排程維持原狀。

固定樣本仍為 Facebook 1703774981107090（不用停損，因為停不掉）及 Threads 4024468641932717746（展示新 GShock，表示下週穩了）。兩筆均尚未嘗試下載／附圖，沒有生成請求、沒有固定格式輸出，也沒有方向、強度、標的、理由或服務回傳的模型／推理資訊。指定 gpt-5-mini／low 僅是請求設定，不能當作實測支援或獨立驗證。前後免費點數、請求額度、token 用量皆未取得；不宣稱零扣點，亦不把點數換算成 tokens。

逐筆與請求紀錄見 data/social_chatanywhere_authorized_smoke_20261107.json。這次不標記貼文處理完成，沒有換模型、略過圖片／格式、切換付費供應商，亦未把官方 OpenAI 金鑰注入一次性 job。

## 後續有限 403 排查

使用者另授權最多 3 次無生成診斷與 2 次生成、無自動重試；本輪實際 3 次診斷及 1 次生成。證據顯示 .org 為 Cloudflare 1010／browser_signature_banned，而官方 .tech 可用同一 Secret 列模型並生成，因此不是 /v1 拼接或免費版一律不能列模型。第一筆服務卻將 low 回傳成 minimal，驗證拒絕後停止，Threads 未送出，不標記完成。完整證據與診斷器停止判斷缺口、必要錯誤記錄修正見 CHATANYWHERE_403_DIAGNOSIS.md；一般 pause、Pages、排程與合併狀態未解除。模型、推理與 token 數僅列為服務回傳／宣稱，免費實際扣點仍未知。

## minimal 後續一次性技術驗證（已停止）

使用者明確接受公開兩筆樣本交由第三方以 minimal 評估。本輪重用 Facebook 保存欄位，新增僅 Threads 生成 1 次（HTTP 200），模型清單／額度查詢 0 次，無重試。請求設定與服務回報分列，未獨立驗證底層模型或推理強度。圖片確實附於請求，但實際視覺理解仍僅有服務聲稱。兩篇維持 direction=0、review；模型對投資關聯及引用欄位有語意品質問題，不能因技術格式成功推定可批次。實際扣點未知。詳見 [本輪驗證報告](CHATANYWHERE_MINIMAL_VALIDATION.md)。一般暫停保持、一次性入口停用，未啟用排程／Pages／合併。OAuth 的使用者畫面證據與權杖保存未驗證限制維持原結論；免費版個人交易研究與商業用途適用性未確認。
