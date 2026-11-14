# 2026-11-14：更新 Apify Token 後續跑受阻

使用者要求繼續補齊至本次執行當下。先驗證金鑰，不啟動收費抓取或 AI。PR 分支沿用原作者規則及現有帳本，沒有重設進度、重送文章或更改 Pine。

## 實測

- 台灣時間 18:11:44，新 GitHub Actions Secret 非空，Bearer Header 僅送往 https://api.apify.com；Facebook 的 `/v2/acts/apify~facebook-posts-scraper` 回覆 HTTP 404。
- 台灣時間 18:14:06，改以同一公開 Actor 的正式 ID `/v2/acts/KoJrdxJCTtpon81KY` 診斷，HTTP 404、application/json，錯誤代碼 `record-or-token-not-found`。不保存原始錯誤內容、Token 或 Authorization Header。
- 不帶金鑰的同一官方 API 公開 metadata 查詢，Facebook、Threads 均 HTTP 200，確認名稱與正式 ID 對應，並非直接判定 Actor 已刪除。
- 正式 ID：Facebook `KoJrdxJCTtpon81KY`；Threads `yacNYZpu9F3C8EATQ`。
- 認證診斷 2 次 GET，無憑證公開 API 對照 2 次 GET；Actor 啟動 0、生成 0、AI tokens 0。Threads 的新金鑰存取未驗證：Facebook 拒絕後立即停止，未繼續嘗試。

## 結論與接續

已確認阻塞在 Apify 存取檢查，不是 AI 額度。無法只憑這個 404 區分 Token 有效性、資源授權 ID、Read 權限或帳戶存取限制，不宣稱單一根因已證實。

使用者影片顯示資源權限的 Actor ID 填入名稱。先前指引未區分名稱與正式 ID，應修正：在 Apify Token 編輯頁，兩項 Actor ID 改為上述正式 ID，各有 Read／Run／List runs；Restricted access 與 default run storages 授權保持，其他權限不擴大。若產生新 Token，更新同一 GitHub APIFY_TOKEN Secret，不把 Token 貼到聊天。修改後先重做唯讀驗證，通過才啟動增量抓取；此建議尚未經修改後實測。

## 保留的進度

雙平台成功抓取截止仍為 2026-11-07 20:15:59.578797（Asia/Taipei），不能宣稱補齊到 11/14。已保存 666 篇：訊號 231、無訊號 306、待確認 99、技術失敗 13、輸入失敗 7、未知 0、尚未處理 10（Facebook 缺媒體）。完整指標與策略仍各 380 事件；不把最新事件時間當作資料完整處理時間。

憑證修復後，從各平台成功截止時間接續，保留兩小時重疊去重；已完成、待確認、技術失敗與未知項目不自動重送。先前已預留媒體網址保留，不因更新金鑰自動重開 Actor。

診斷帳本：`data/history_media_repairs/replacement-token-check-20261114.json`、`data/history_media_repairs/scoped-id-check-20261114.json`。兩個本次診斷 workflow 已停用；未啟用持續排程、發布網站、Telegram 或合併 PR。這次只新增診斷紀錄，正式游標／用量帳本／事件／Pine 均未變。

依據：[Apify scoped token 文件](https://docs.apify.com/integrations/api#api-tokens-with-limited-permissions)、[Facebook Actor](https://apify.com/apify/facebook-posts-scraper)、[Threads Actor](https://apify.com/automation-lab/threads-scraper)。
