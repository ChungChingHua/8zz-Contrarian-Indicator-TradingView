> 現行 Apify 政策已更新：取消程式單次費用與每月啟動上限，保留去重、記帳與失敗停止。見 [APIFY_LIMIT_POLICY.md](APIFY_LIMIT_POLICY.md)。以下歷史用量及驗收數值不是本次新執行結果。

# PR #1：Telegram、增量佇列與看板驗收

© hansai-art / Group.G；原作者署名、MPL-2.0、原作者完整提示及十組範例保留。本文件為目前操作入口；舊 AUTOMATION.md 的 smoke／付費 OpenAI／歷史批次步驟不是本輪啟用方式。

## 交付狀態

接續 `codex/social-pipeline-20261106`，基底 `331e8b3`，同一 PR #1。核對 GitHub 遠端摘要與本地帳本一致：666 篇，250 篇完成（108 有訊號／142 無訊號）、54 待確認、7 技術失敗、1 媒體前檢失敗、354 未處理／352 去重組。原作者歷史 151＋既有 AI 106＝257 事件，沒有重判。兩平台成功抓取窗仍至台北 2026-11-07 20:15:59，最新訊號 2026-09-03 13:38:49。

本輪實際外部 Apify 0、AI 0、Telegram 發送 0，歷史未前進。僅讀取 GitHub 與 TWSE 官方交易日資料。行情沿用已保存快取，沒有假造新行情。沒有啟用正式排程、部署網站、合併 PR，也沒有執行 Telegram chat_id 探索或測試。

實作包括：手動 Telegram 設定／單次測試；官方交易日檢查；雙平台獨立增量成功截止與預算；沿用原 worker 的新文章專用佇列；GitHub CAS 預留與 unknown；共用保存事件／Telegram outbox；失敗通知獨立續接；257 事件看板、兩種績效時間基準及開啟頁面的 30 秒更新；桌面／手機與明示模擬資料的預覽。

## 現在如何預覽

- `docs/8zz-dashboard-preview.zip`：下載、解壓縮、雙擊 `index.html`，可離線操作。另有 `validation-preview.html`，頂部明示「模擬資料」，用來驗收多／空虧損、平手、勝與未平倉；不是投資結果。
- `docs/preview.html`：真實保存的 257 事件單檔預覽，資料與程式內嵌，不發送外部請求。
- `docs/previews/desktop.png`、`mobile.png`：1440×1100／390×844 的實際 Chromium 全頁截圖。
- `docs/previews/validation-desktop.png`、`validation-mobile.png`：同畫面明示模擬資料。
- GitHub 的 HTML 原始碼頁不會直接渲染，請下載 ZIP 解壓縮。沒有發布新公開網址。

本機預覽支援開啟後自動取得新保存資料：

```sh
git checkout codex/social-pipeline-20261106
python -m http.server 4173 --directory docs
```

開啟 `http://localhost:4173/`。HTTP 入口每 30 秒以 `cache: no-store` 抓 `dashboard-data.json`，回到前景也更新；不重整頁面即可改變事件／曲線／新鮮度。更新失敗保留已顯示快照並提示。內嵌預覽刻意保持離線。正式主機將來必須提供新的 JSON 才有新資料；本次 Pages 仍停用，不宣稱已發布頁面會更新。

## Telegram：取得 ID、設定 Secret、獨立測試

沿用已註冊的 `.github/workflows/fetch-fb-events.yml`／**Social update (bounded)**，僅新增 Telegram 專用動作，預設 `status` 不連外。這避免新 workflow 在預設分支尚未註冊而無法手動執行的常見問題。入口不注入 Apify 或 AI Secrets。

1. GitHub → Actions → Social update (bounded) → Run workflow，分支選 **codex/social-pipeline-20261106**，action 選 **telegram-discover**。只讀 `TELEGRAM_BOT_TOKEN`，先查 webhook，再呼叫 getUpdates，不送訊息、不設 offset、不刪 webhook。
2. 若 UI 仍顯示預設分支的舊輸入欄，已登入 GitHub CLI 的使用者可明確指定分支版本：

   ```sh
   gh workflow run fetch-fb-events.yml --repo ChungChingHua/8zz-Contrarian-Indicator-TradingView --ref codex/social-pipeline-20261106 -f action=telegram-discover
   ```

   本輪沒有執行這條命令。若 GitHub 尚未允許此分支 dispatch，就保留程式，待工作流程註冊後執行；無須因此啟用抓取或合併本 PR。也可在自己的安全環境設定環境變數後執行 `python scripts/telegram_notify.py discover`；GitHub Secret 無法下載明文，不要把 Token 貼在聊天、命令列參數或檔案。
3. log 只列候選私人 **chat_id** 和固定狀態，不列 Token、API 完整網址、完整回應、聊天名稱或訊息文字。多個 ID 由你確認，程式不猜。沒有訊息就回 @WS_8zz_Alert_bot 再傳文字；最多讀取 100 updates，飽和會標示 bounded_updates，不宣稱列出所有候選。
4. webhook 已設定或 getUpdates HTTP 409 接收衝突時停止，請先核對現有接收程式；不擅自變更。不要為了取得 ID 刪除既有 webhook。
5. 確認後到 Settings → Secrets and variables → Actions → New repository secret，名稱 **TELEGRAM_CHAT_ID**，值填剛確認的正整數私人 ID。不要把它改填群組或頻道 ID。
6. 之後你決定測試時，單獨執行同 workflow，action **telegram-test**。讀取兩個 Secrets，先以 getChat 確認私人聊天室，再只發送一次 **「8zz 通知串接成功」**。沒有自動重試。這次交付沒有執行此步，也不能宣稱串接成功。

測試入口每次手動執行都代表一次新測試；不要因網路回應不明直接按 Re-run。正式訊號另有 durable outbox 防重送。

## Secrets 與缺項

| 名稱 | 用途／目前狀態 |
|---|---|
| TELEGRAM_BOT_TOKEN | 使用者已設定；本次未讀取明文或線上驗證 |
| TELEGRAM_CHAT_ID | **尚缺，需使用者確認候選後設定** |
| APIFY_TOKEN | 沿用既有；本次未啟動 Actor 或讀取 dataset |
| CHATANYWHERE_API_KEY | 沿用既有免費金鑰；固定 `.tech/v1`、`gpt-5-mini`、minimal、strict schema。免費額度阻塞仍保存，未驗證恢復 |
| github.token（自動） | workflow 的 contents:write，用於遠端 CAS 帳本；不需新增 GH_TOKEN Secret |

不需要新增付費 OpenAI／Google Secret，不更換模型或供應商。不從模擬測試推論 Secrets 有效。

## 排程與預設停用

`live-update.yml` 已寫入 UTC cron，對應 Asia/Taipei 08:45、09:00…13:30，每 15 分鐘、包含首尾，共 **20 個時段**。工作日 cron 先喚醒，再查 TWSE 官方表，並非只排除週末。08:45 從各平台上次**成功完成窗**減 2 小時重疊開始，涵蓋夜間、週末與假日；不是從當日 00:00 或最新貼文猜截止。

**兩道閘門均預設關閉**：`data/live_settings.json.enabled=false`；repository variable `LIVE_PIPELINE_ENABLED` 必須明確為 `true`。只提交程式／開 PR 不開始抓取。新排程只會由預設分支的 workflow 觸發；本 PR 未合併，未註冊正式 cron。未來啟用仍須使用者驗收後另行決定，不要為測試 Telegram 打開這兩道閘門。

GitHub Actions cron 可能排隊、延遲、甚至遺漏，不保證 08:45 準時或即時；15 分鐘是目標頻率。程式以當下台北區間辨識時段，重複／已預留時段不再執行，不製造付費補跑；晚於 13:30 的新執行跳過。延遲期間貼文留到下一個成功增量窗。Actor 最多短暫輪詢約 48 秒，未完成保留 run ID，下個時段接續；最後一輪仍可能延到下一交易日才取得結果。

TWSE 來源為 `https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=json&queryYear=115`，保存來源與 hash。年度表包含平日國定假日、補假、春節前無交易但有交割日，以及開始／最後交易日；未知格式拒絕，不猜。每個正式抓取入口先重新取得官方表，快照最多有效 24 小時；缺資料、過期、錯年度或取得失敗明確停止，付費抓取 0。離線可用保存表驗證；過期快照不能解鎖正式抓取。

年度表不保證涵蓋臨時颱風休市等公告。`closure_overrides` 支援附公告理由的指定日停用；遇臨時休市須核對 TWSE 公告並停用流程或加 override。此自動公告整合**尚未實作／線上驗證**，不能把年度表宣稱為完整即時停市服務。

正式流程與既有歷史 worker 共用 concurrency group `original-author-history-batch-01`，不取消正在保存狀態的工作。資料用 GitHub Contents SHA CAS，ACK 預留後才進付費請求；衝突停止，不刷新 SHA 覆蓋別人的進度。GitHub concurrency 對 pending runs 的替換／不保證排序可能減少實際輪數；增量截止補上漏掉的時間，不增加付費追趕輪次。

將來的啟用步驟（**本輪未執行**）：先補 chat_id、完成單次 Telegram 測試、確認官方交易日及臨時休市管理、免費額度與預算可接受，再經使用者決定註冊／整合預設分支 workflow；修改 enabled 並設定變數 true。程式仍寫回本 PR 分支，若之後搬移分支，需同步 h.BRANCH、checkout ref、GitHubStore 與 dispatch 分支保護，不能只改一處。

停用：將 LIVE_PIPELINE_ENABLED 改 false 或 enabled 改 false；既有工作不會因此立即取消，若中斷執行，先核對 unknown 與遠端預留。網站發布仍是獨立選項，deploy-pages.yml 仍有 false 閘門。

## 用量與費用估算（不提高既有限額）

| 項目 | 每日 20 輪／兩平台的量級 |
|---|---|
| Actor 啟動需求 | 一般完整空窗也可能需啟動 run：40 runs／交易日；20 個交易日約 800 runs。分頁／前次未完成會改變實際啟動數，並非每個 cron 必定 2 runs |
| 每 run 限制 | 維持 180 秒、512 MB、maxItems 50、restartOnError=false；不傳 maxTotalChargeUsd |
| 最多回傳量級 | 若每次均到 50 筆，40 次約 2,000 列／日，含重疊／重複；不等於新文章數或 AI 次數 |
| 運算資源量級 | 若每 run 都用滿 180 秒／0.5 GB，約 0.025 GB-hour／run，40 次約 1 GB-hour／日；僅資源量級，不是帳單 |
| AI | 只送新文章佇列；每輪最多 5、每篇一次，400 月嘗試上限維持；優先核對 durable 作者帳本，不把 legacy usage 當完整總量。無新文 0；額度／服務故障立即停，不切付費備援 |

**實際付費模式／單價未重新核實，無法提供可信的每日帳單報價。** 已移除程式單次 US$0.10 與每月 70 runs 上限，無固定日／月美元上限可由此推算。啟動與費用仍記帳；帳戶額度不足或認證／服務失敗仍停止，不會自動儲值。既有成功 run 約 0.022／0.020 USD 僅是歷史觀察，不能當成固定費用或最新扣款。

## 狀態與安全續接

- `data/live_control.json`：各平台 completed_until、固定窗口、page_before、run ID、預留、錯誤、時段與 AI stop。50 列飽和分頁、費用截斷、格式缺失、run 失敗或 POST 不明都不推進來源截止。先保存貼文並得到 ACK，才更新成功截止。一般重跑以來源 ID 去重，內容變動隔離。
- `data/live_posts.json`／`live_plans`／`live_progress`：新文章獨立佇列；不選歷史 pending。原始發文、抓取、真正完成判讀時間分開保存。沿用原作者 fingerprint，圖片仍須實際供給原 downloader／模型；影片與失敗圖片明示未分析。不把 OCR 或未下載媒體當成已分析。
- 失敗／待確認／矛盾不產生訊號、不自動重送。連續三篇格式／媒體錯誤停止；共同設定錯誤、服務拒絕／額度或傳輸不明立即停止。工作中斷後會檢查已保存 live worker 的停止紀錄，不因漏寫 control 就繼續消耗。
- 免費額度恢復後，先核對帳本、金鑰仍為免費與可用額度，再在已另行啟用的 live workflow 手動 action `resume-ai`，只解除 AI stop，不發請求；下一輪只選未送出新文章。已完成、待確認、失敗、unknown 不重送。歷史仍須獨立授權入口，本輪不補跑。
- Apify `submission_unknown`：先至 Console 核對原 run；確認同一 run 後填回 active.run_id、submission_unknown=false，人工解開 blocked；已失敗／截斷 run 先查 dataset 與費用，不能直接刪掉狀態再付費重跑。只有確認沒有送出才可解除原預留；預算不自動退還。
- `data/signal_events.json` 是保存事件，Telegram 和網頁共用；原 257 事件列 baseline，首次啟用不大量推送舊訊號。新文章若跨台北日期才完成判讀，保守標示歷史補判讀（僅通知標籤，不改情緒條件）；舊歷史 worker 事件同樣標示歷史補判讀。網頁仍保留全部 baseline。
- `data/telegram_outbox.json`：pending／unknown／sent／failed／baseline_suppressed。先以遠端 ACK 保存 unknown 才送；已送不再送。認證／聊天設定錯誤／429 等明確拒絕為 failed，傳輸／服務端／不完整回應為 unknown。Token 不進狀態，接收者只保存 hash。
- 修復通知後，action `retry-notifications` **只把明確 failed 改回 pending**；再 action `notify` 只讀已保存事件並通知，不抓取、不呼叫 AI。unknown 永不自動改 pending，需人工核對。Telegram 沒有本流程可用的發送冪等鍵：若已發送但 ACK／保存失敗，可能「已收到、帳本仍 unknown」。本實作選擇不自動重送以避免重複；人工重送、不同 workflow 手動 test 或重建／遺失帳本仍可能重複，無法保證 exactly once。
- 缺 Telegram Secret 顯示未設定，事件與判讀結果仍保存。通知失敗不撤銷事件、不重新 AI。GitHub CAS／帳本容量（單文件 900KB）或服務故障立即停；未來大量資料需分片遷移，不能悄悄刪除防重送紀錄。

## 看板計算核對

Mode A 的 17、signalLifeBars 的 24 與關閉的三個濾網，已逐一核對原作者提供版、根目錄 Pine、最新候選及 README，沒有猜新值。17 是圖表 K 棒，網站 A 限 30 分鐘；24 只控制視覺有效性。Mode B 原定方向翻轉出場；網站 B 明示日線代理，Pine 依圖表週期，不能宣稱二者完全相同。原作者面板硬編碼的勝率未複製。

事件不是交易；同向追加不進場，同收盤合併最後方向，單部位 100% 名目本金、不重疊、不實際加碼；已結算按淨值複利，持有中標記浮動。所有原標的（含未辨識）明示 →0050.TW 代理，不將不同股票報酬相加冒充帳戶績效。多空損失都敗，平手獨立，未平倉不進已結算分母。未含手續費、稅、滑價、股息、借券及融資限制。

歷史發文參考：257 事件，B 56 次進場／55 結算，35 勝／20 敗／0 平手，勝率 63.6364%，平均 +0.46131%，1 未平倉浮動 +13.3895%；曲線約 138.15，0050 比較約 148.48。行情仍截止台北 2026-11-06 13:30，**部分資料績效**，不是截至今天或新模型驗證。A 92 個翻轉候選缺覆蓋期間 30 分鐘行情，沒有假曲線。

可成交時間參考：既有 257 筆都缺逐篇完成時間，所以目前 257 筆獨立列缺完成時間、0 可驗證交易，沒有補成發文時刻、dispatch 時刻、檔案時間或現在。新 worker 往後才保存真正 completed_at。成交嚴格晚於發文及完成時間，已錯過收盤不回填。兩條時間基準分別排序；已完成時間序列與發文順序可能不同。

離線重建：`python scripts/build_audited_dashboard.py`；只更新必要行情：`python scripts/build_audited_dashboard.py --refresh-market`（未在本輪執行）。行情失敗會列 errors／缺資料，不偽造數據。`build_site_data.py` 舊口徑不作本看板依據。

## 驗證與仍未線上驗證

170 項 unittest 通過；其中 25 項新增回歸，涵蓋交易日／20 時段／過期、兩來源截止、夜間週末窗、重疊去重、飽和與費用截斷、預算、重複時段、CAS、無新文無 AI、原作者 fingerprint、完成時間不捏造、Telegram 候選／衝突／遮蔽／私人驗證／失敗／unknown／發送後保存中斷。Apify、AI、Telegram 外部存取均 mock。

桌面及手機 Chromium 通過：無水平溢出、無 JS 錯誤，日期／平台／方向／強度／關鍵字入口保留，平台與關鍵字操作、模式／時間基準切換、既開頁面接收更新、poll 失敗保留快照。內嵌預覽無外部請求。`data/live_browser_validation.json` 保存結果。

模擬 5 事件：4 結算＝1 勝／2 敗／1 平手、勝率 25%、1 未平倉；起始100→90→80→80→88，最後含浮動92.888889。清單、統計與曲線一致，`data/live_offline_validation.json` 保存逐筆明細。模擬失敗通知只更新 outbox，不呼叫 AI。

仍未驗證：真實 Telegram chat_id／Secrets／單次發送、Apify 與免費 AI 正式串接、正式 cron 延遲與費用、臨時休市自動公告、較長歷史 30 分鐘行情、TradingView 編譯、正式網站託管與輪詢。**完成程式與離線驗證不等於以上線上串接已成功。**
