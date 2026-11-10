# 網站自動更新與發布準備

本次只完成實作、保存資料重建與本機預覽。沒有 Apify／AI／Telegram／行情外部呼叫，沒有啟用正式流程、發布 Pages 或合併 PR #1。

## 資料路徑

1. `live_pipeline.acquire` 先取得 GitHub 保存 ACK，才推進各平台成功抓取截止。
2. 每輪判讀前先 `refresh_outputs`：從已保存文章與既有判讀產生待判讀清單。判讀完成後再次產生輸出；未處理、待確認、失敗、unknown 都不轉為多空訊號。保留原歷史基準事件與中性觀察，新增多空仍須通過原作者政策與既有有效性驗證。
3. `history_completion.report` 從歷史與新文章的持久判讀帳本建候選；遠端歷史報告保存也接至相同網站輸出函式；`build_audited_dashboard` 生成 `data/signal_events.json`。Telegram 讀這份保存事件；網站只作公開投影與既有績效計算，不重新呼叫 AI。
4. 網站輸出只保留事件、行情／績效、文章狀態、各平台截止、必要公開進度。排除原始帳本、內部路徑、服務回應、token 用量、完整通知設定、API Key 與媒體附件授權網址。公開來源連結清除授權 query。
5. 公開內容的 SHA-256 決定版本；內容未變時保留原建置時間與版本。先保存不可變的 `snapshots/<version>.json`，最後保存 `data-version.json`。初始 HTML 用同版本 bootstrap，離線 `preview.html` 不連網。
6. HTTP 網頁每 **60 秒**只讀小型版本檔（時間 query + `cache: no-store`）；版本不同才讀對應快照。15 秒逾時、HTTP 錯誤、版本不一致或無效結構不替換畫面。既開頁面保留目前日期／平台／方向／強度／關鍵字、績效模式、時間基準及待判讀篩選；頁碼保留到有效範圍。回到分頁時另檢查一次。背景分頁會受瀏覽器節流，不保證每分鐘準時。
7. 更新失敗顯示最後成功版本，下一輪重試；成功後重新繪製清單、全樣本統計與曲線。篩選只影響清單與篩選統計，延續原看板揭露。
8. 行情失敗保留既有對應週期資料，列出錯誤；「最後成功取得」「行情截止」「網站版本／重建時間」分開。資料版本前進不宣稱行情／績效已更新。保留部分資料績效、0050 全部代理、17 根 30 分鐘 A／日線 B、非重疊部位、複利與費稅限制。

## 明確且有條件的 GitHub Pages 部署

`deploy-pages.yml` 不設每日重新部署。僅在 main 公開檔案 push、Live incremental update／既有歷史續跑完成，或手動 dispatch 時檢查；`PAGES_PUBLISH_ENABLED == 'true'` 且 workflow 位於 main 才可進入。workflow_run 也處理失敗輪次已保存的待判讀進度，不能因此推斷抓取／AI 成功。

- 資料 workflow 的 GitHub token commit 不會觸發一般 push workflow，因此另用 **workflow_run** 明確銜接；來源分支限制為 main 或現有 PR 分支。
- 只打包 `index.html`、CSS、前端 JS、bootstrap JSON/JS、版本檔、該版本快照及 `.nojekyll`，**不整包部署 docs/**。報告、ZIP、原帳本、設定、截圖都不在公開 artifact。
- 打包時核對版本檔、快照與 bootstrap JSON 一致，避免資料寫到一半部署。
- 對整個公開 artifact 計算 digest；與 `pages-deployment-state` 的最後成功發布 digest 比較。無變更就跳過 artifact 上傳與 deploy job。首次尚無 marker 才視為需要部署；狀態 API 其他錯誤直接停止，不猜測為有變更。
- 透過 `actions/upload-pages-artifact` 與 `actions/deploy-pages` 明確部署。成功後才寫入獨立的 `pages-deployment-state` 孤立分支（只有公開 digest）；不使用有到期日的快取作唯一判斷。所有 Pages 工作序列執行，失敗不推進 digest。若網站部署成功但 marker 寫入失敗，該次 workflow 失敗，須先核對部署並修復 marker，再重跑，避免不必要重部署。
- 前端輪詢只會請求靜態版本與快照，沒有任何抓取、AI 或通知端點。

## 正式發布前需設定（本次均未執行）

1. 審查並合併 PR 後，確保新版 `deploy-pages.yml` 與 live workflow 存在於預設 main；GitHub 的 workflow_run 與 cron 需要預設分支上的 workflow。現有正式程式仍固定寫 `codex/social-pipeline-20261106`，live checkout 也使用該分支；本版部署會從完成的 live workflow 分支取最新已保存快照。若日後統一搬到 main，須一起修改 `history_worker.BRANCH`、workflow checkout、所有分支授權／操作文件，不能只改單一設定。
2. Repository Settings → Pages → Source 選 **GitHub Actions**；確認 github-pages environment 的允許部署分支與審核者設定，允許實際工作流程 ref main。確認組織政策允許所固定 SHA 的 Actions、artifact 上傳與 OIDC。
3. 準備 `PAGES_PUBLISH_ENABLED=true`（**尚未設定**）；工作流 prepare 只需 contents:read，deploy 需 pages:write、id-token:write，以及成功後寫 digest 所需 contents:write。`pages-deployment-state` 分支規則須允許 GITHUB_TOKEN 快轉寫入；不得刪除或隨意改動 marker。
4. 首次在 main 明確手動觸發 Pages 工作流；驗證公開 artifact 白名單、Pages 正式 URL、快取及既開頁面更新。這項實際 Pages/CDN 驗收尚未做；本次只有本機 HTTP 驗收。
5. **抓取／AI 啟用是另一項授權**：維持 `data/live_settings.json.enabled=false` 與未啟用 `LIVE_PIPELINE_ENABLED`。日後另行確認交易日表、Actor 費用／每月保護上限、AI 免費額度、錯誤續接與 Telegram chat_id，再設定必要 Secrets（APIFY_TOKEN、CHATANYWHERE_API_KEY、TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID），不能放到網站。每月 70 Actor runs 仍不足每日 20 輪，未調高。本次沒有修改正式 schedule、控制、用量或 outbox。
6. 行情採獨立 `refresh-market` 動作；目前 run 不自動抓行情。若要定期更新績效，正式啟用前須另定行情更新頻率與額外成本／資料授權，不能把新訊號網站更新當作行情更新。

## 可預期延遲

| 階段 | 一般預期／限制 |
|---|---|
| 新文章被抓到 | 現有交易時段每 15 分鐘一次，正常約 0–15 分鐘加 Actions 排隊與 Actor 執行；非交易時段等待下一交易時段。GitHub cron 可延遲或漏跑，沒有即時 SLA。 |
| 判讀與保存 | 視佇列、媒體、供應商回應及額度；沒有固定保證，quota／unknown／失敗會停住並保留狀態。 |
| 後端快照與 Pages | 保存後等該輪 workflow 完成，再排隊打包部署；小型網站通常約 1–5 分鐘，另受 environment 審核、GitHub／CDN 故障影響，非保證。 |
| 已開網頁 | 部署可取得後，前景分頁通常再 0–60 秒，加請求時間；背景節流、網路斷線、CDN 舊版本可能延後，會保留舊資料。 |
| 績效 | 只在另行取得新且有效的完成行情後反映；B 日線在完成收盤後，A 需完整 30 分鐘行情；尚未更新行情就沒有績效更新承諾。 |

因此「判讀已保存」到前景網頁可見，正常可估數分鐘加最多一輪 60 秒檢查，**不是抓取後 60 秒內一定更新**。

## 私人存取方案

GitHub Pages 本案按公開網站設計；所有部署資產與來源資料均應視為可下載。不以隱藏網址、前端密碼或把 repo 設為私人當作網站保護。若需私人戰績，建議把這份公開投影放到具伺服器端身分驗證的託管服務（例如 Cloudflare Access + 受保護靜態來源），並保護 JSON 與快照的每個路徑；原始帳本與 Secrets 存在私人後端。或先確認 GitHub Enterprise 的私人 Pages／組織存取能力是否適用。未選定方案前不發布私人內容。

## 驗證與預覽

- `python -m unittest discover -s scripts -p 'test*.py'`：194 項通過；含公開白名單、可重現版本、不變不部署、進度變更及行情失敗保留測試。
- `node --check docs/dashboard.js`。
- 本機 `python -m http.server 8000 --directory docs` 後執行 `python scripts/verify_dashboard_refresh.py`。使用 Chromium 與瀏覽器虛擬時鐘走實際 60 秒 interval，沒有直接呼叫刷新函式或重新載入頁面。模擬 HTTP 回應，零外部請求。
- 1440×1100、390×844：版本不變不抓快照；新版本更新清單／統計／曲線；保留篩選與模式；503／無效快照／較舊快取保留資料；恢復後續更；無 JS 錯誤／橫向溢出。機器結果：`docs/previews/auto-refresh-validation.json`。
- `docs/preview.html` 是可下載的單檔離線預覽（不連網、不輪詢）；HTTP 使用 `docs/index.html` 才會輪詢。
- 桌面／手機：`docs/previews/desktop.png`、`docs/previews/mobile.png`；截圖恢復使用真實保存資料，測試中的模擬數字未保存到正式資料。
