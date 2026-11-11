# 2026/11/11 圖片阻塞根因診斷

**Threads 已確認是圖片網址簽章過期；Facebook 已確認在 TCP 連線階段受阻，尚無 HTTP 回應可判定其簽章狀態。** 本次沒有呼叫 AI、Apify、Telegram 或行情服務，沒有恢復歷史判讀、排程、網站部署或 PR 合併。

## 實測證據

執行時間：**2026/11/11 17:27:26～17:27:37，Asia/Taipei**。沿用既有網域白名單、公網 IP 固定及 TLS 憑證／主機名驗證，不使用 cookie 或 API 金鑰、不改寫簽章參數、不跟隨重新導向；每次最多讀取 4096 bytes。

| 來源貼文 | 實測結果 | 可以確定的原因 |
|---|---|---|
| Facebook `1660785808739341` | `scontent-ord5-2.xx.fbcdn.net` 的首個 IPv4 在 TCP connect 階段 10.010 秒逾時；另一個經驗證 IPv6 立即 errno 101 | worker 到該 CDN 位址無法建立 TCP 連線；還沒進入 TLS／HTTP |
| Threads `3992201729433763729` | TCP 0.064 秒、TLS 0.066 秒完成，HTTP 403，text/plain | CDN 明確回覆 **`URL signature expired`** |
| Threads `3992213198011063292` | TCP 0.063 秒、TLS 0.064 秒完成，HTTP 403，text/plain | CDN 明確回覆 **`URL signature expired`** |

兩個 Threads 回應均為 21 bytes，SHA256 都等於 `16366d2552aa8349747c1168a3ef03665652b08d80385b6664c4cbf6a5b2f932`；離線計算確認它精確對應上述固定錯誤字串。沒有把未知錯誤 body 或簽章 URL 寫進日誌。

兩個 Threads URL 的 oe 時間戳提示分別為台灣時間 11/11 11:22:07、07:34:38，均早於實測，且與 CDN 的簽章過期回覆一致。Facebook URL 提示為 10:19:12，但因尚未收到 HTTP 回應，**不能只憑時間戳就斷言這次 Facebook 逾時也是簽章驗證造成**。

Facebook 在送出 HTTP URL 前就卡在 TCP；現有證據無法細分是 runner 出口、網路路由或 CDN 節點丟棄連線。IPv6 備援也不可達，僅增加 IP fallback 並不能保證解決這個樣本。沒有證據顯示 TLS 驗證、圖檔格式或 ChatAnywhere API 在這一步拒絕圖片。

## 為何續跑仍拿到舊網址

1. [history_completion.py 第199行](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/blob/codex/social-pipeline-20261106/scripts/history_completion.py#L199) 從固定 Git 快照 `51e27179cc4fa3447ce9e011c2e7d194ad5a9520` 取得原文及媒體，確保舊資料不被改寫。
2. [restore_saved_history_media.py](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/blob/codex/social-pipeline-20261106/scripts/restore_saved_history_media.py) 只讀控制帳本中兩份已保存增量 Dataset；它沒有重新取得這些 9 月貼文目前的圖片網址。
3. 目前保存的是帶期限的 URL，沒有足以供續跑使用的圖片檔案快取。更新 AI 額度後，下載器仍會用原快照的舊網址。
4. 下載失敗發生在生成之前；三篇 attempts=0。連續三筆觸發既有共同故障保護，因此停止，而非把未讀圖片宣稱完成。

離線掃描固定快照中 **411 篇可辨識首張圖片的貼文**，其首圖 URL 的 oe 提示全部早於本次執行；找不到同主機、提示仍在未來的圖片作為對照，所以沒有發出這兩個預備對照請求。這不是對全部 411 個 URL 都做 HTTP 驗證；確定簽章過期的實測證據限於上面兩個 Threads URL，也未涵蓋其他 Dataset 或所有多圖附件。

## 恢復所需修正

- 為受阻／尚未判讀貼文取得目前可讀的媒體網址；新的網址取得後立即下載成受控快取，保存內容 hash、來源及取得時間，避免跨日只依賴短效 URL。
- Facebook 先驗證 worker 能連到新網址對應的 CDN。Threads 需要更新已過期簽章；持續重試同一舊網址不會更新簽章。
- 媒體恢復後，先驗證少量下載與格式，再從未送出的項目接續。三篇零生成失敗需單獨核對後恢復，已取得 AI 回應的一篇不重送；原始回應、失敗與恢復紀錄分開保存。
- 本次只診斷，未啟動付費抓取以更新網址，也未放寬 TLS、網域、IP、大小、逾時或圖片誠實標記規則。

## 範圍與可追溯性

- 本次上限 6 次圖片 GET 嘗試，實際 **4 次連線／GET 嘗試**：2 次收到 HTTP 403，2 次在 TCP 階段失敗。DNS 查詢與 GitHub 讀寫另計，不能把 4 當成服務端確實收到的 HTTP 次數。
- AI 生成 0、Apify Actor 0、其他供應商 API 0；沒有讀取它們的 Secret。未保存完整 URL、query、任意錯誤 body 或圖片 bytes。讀取影像前綴是傳輸診斷，不是圖片判讀。
- 比對診斷前後 **38 個**歷史帳本、控制、正式資料、用量、Pine 與通知檔案的 Git blob SHA，全部不變。未重新標記任何貼文完成。
- [完整結構化證據](../data/history_media_rootcause_20261111.json)。一次性診斷入口完成後停用；PR #1 保持未合併。
