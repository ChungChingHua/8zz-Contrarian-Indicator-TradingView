# 已架設網站的後續更新

事件清單新增「是否交易：全部／是／否」篩選，依當前標的、模式及時間基準的保存交易狀態判斷；只影響清單與篩選統計，版本更新時保留選擇。Mode B說明已改為以各標的日盤收盤價模擬進出場（台指13:45、0050 13:30）。

最新：已接永豐保存行情並加入0050／台指期貨TXFR1切換，詳見 [SHIOAJI_MARKET.md](SHIOAJI_MARKET.md)。

網站已成功發布：https://eightzz-september-dashboard.yummyguppy7.chatgpt.site （僅擁有者可登入查看）。

使用者已要求直接架設，之後由助理依使用者指示更新同一網站；不需要使用者手動上傳檔案。GitHub Pages 建立 API 回傳 403（GitHub integration 缺少 Pages 管理權限），因此改用 Sites，維持新站預設的僅擁有者可存取。PR #1 不合併，抓取、AI、正式排程、通知維持停用。

網站身分及最後發布結果保存在 `data/site_release.json`；真正的 Sites 來源 checkout 為 `/workspace/sites/8zz-september`，其 `.openai/hosting.json` 保存同一 project_id。未來必須重用，不能建立另一個網站。若本機來源消失，先取得該 project_id 的既有來源與寫入憑證。

## 資料範圍

- `data/publication_policy.json` 將發文與績效行情限制在台北時間 2026-10-01 00:00 **以前**，即九月底以前。
- 294 個已保存事件、455 篇範圍內文章。成功判讀：145 篇有訊號、191 篇無訊號；66 篇待確認、7 篇技術失敗、1 篇輸入失敗、45 篇尚未開始。**不宣稱九月底已全部判讀完成**。最新成功判讀對應發文為 9/22 21:50:05，最新訊號為 9/22 18:54:02（台北時間）。
- 新近抓取的十一月文章與十月文章都不得出現在網站事件、待判讀清單、計數或績效中；行情、曲線、交易價位也依相同上限重算。判讀完成時間與網站重建時間可能是十一月，這是操作時間，不是十一月來源文章。
- 保留完整後端保存資料與 Telegram 共用事件，不刪除原帳本。網站篩選在後端績效模擬前執行，並在部署打包時再次驗證，不依賴前端隱藏。

## 使用者再次要求更新時

1. 讀取這份文件、publication_policy 與 site_release，取得相同網站。單純「更新網站」代表從已保存結果更新，不代表授權啟動 Apify、AI 或 Telegram，也不代表解除九月底範圍限制。
2. `python scripts/build_audited_dashboard.py`（不加 `--refresh-market`）從保存資料重建。網站不重新呼叫 AI。若使用者另行明確要求補判讀，沿用原作者政策、額度及持久帳本規則處理，不重送已完成或 unknown。
3. 驗證 `python -m unittest discover -s scripts -p 'test*.py'`、JavaScript 語法與 publication_scope 邊界。新增或修正九月底範圍內的保存資料才進網站；十一月仍排除。若使用者要求擴大日期，須確認其明確指示與先前排除十一月的限制如何並存，不能默認解禁。
4. `python scripts/public_dashboard.py docs /workspace/sites/8zz-september/dist` 只複製公開白名單。保留該來源 `.openai/hosting.json`，不得把 data/、報告、原帳本、Secrets 或舊快照放入 artifact。
5. 依 Sites 技能取得同一 project_id 的短期來源憑證；只經 stdin 傳遞，不寫入檔案或 Git URL。推送這份新來源，從完全相同 commit 打包 `.openai/hosting.json` 與 dist/，保存版本並以僅擁有者模式發布。保持原存取範圍。
6. 查至部署成功，記錄 commit、version、deployment、URL 到 site_release，並回報本次新增多少事件、未完成多少、是否有新行情。內容沒有變動則不需要重部署。
7. 已開網頁會在下次版本檢查載入新快照，保留篩選；離線檔不會自動更新。

## 本次驗證

197 項離線 unittest 通過，包含排除十月／十一月的事件、文章、行情、曲線與部署打包保護。部署 archive 確認 455 篇、294 事件、零十一月來源文章，且不含原始帳本。沒有呼叫 Apify、AI、Telegram 或行情服務。Managed Sites 預覽 relay 在 port 4173 啟動逾時，`sites-preview status` 顯示 stopped；本次新發布範圍的瀏覽器預覽尚未驗證，不以舊的全範圍截圖當作本次驗收。
