> 目前 PR 使用獨立 ChatAnywhere 免費版設定，僅允許兩筆 smoke、無排程及批次。見[目前供應商設定](CHATANYWHERE.md)；先前 OpenAI 官方說明保留作歷史參考。

# Facebook + Threads 更新操作

© hansai-art，保留原指標與 Mozilla Public License 2.0；新增程式同採 MPL-2.0。

## 已匯入與尚未判讀

2026-11-06 提供的 Facebook 285 筆，作者 ID `100044238139017` 符合 284 筆，排除其他作者 1 筆；Threads 399 筆，排除回覆 24 筆，保留 375 筆。兩份資料都涵蓋 2026-07-20 起；這是所提供資料的涵蓋範圍，無法證明平台沒有隱藏、刪除或遺漏貼文。

`data/social_posts.json` 保存原文、ID、來源網址、UTC 與 Asia/Taipei 時間、附件、引用內容、內容雜湊及判讀狀態。留言不納入。初始 659 筆是 pending，不是假裝已完成圖片或 AI 判讀。模型成功且有明確投資情緒才產生訊號；圖片必須實際下載傳給模型，失敗留 retry；社群 CDN 網址會到期，歷史附件失效時須重新匯出該貼文資料／更新附件網址後重試，不能用 OCR 欄位代替；影片待人工處理。OCR 描述不作為已讀圖證據。

`data/historical-indicator.pine` 保存原歷史與署名；每次以此範本和成功標註重新產生完整 `8zz-indicator.pine`。不要直接編輯產物：若需修正舊事件，編輯歷史範本後再生成。

跨平台僅合併 48 小時內、完整文字相同且成功判讀方向相同的貼文；有附件或引用時還須內容雜湊相同。保留所有成員、網址與最早時間於 `social_groups.json`。採保守合併，跨平台圖片 CDN URL 不同可能仍保留兩筆，避免不同立場誤合併。pending 尚無可靠立場，先各自保留。

## GitHub Secrets 與第一次驗證

在本儲存庫 **Settings → Secrets and variables → Actions** 確認：

- `APIFY_TOKEN`：可啟動兩個 Actor、讀取 dataset。
- `OPENAI_API_KEY`：可呼叫 OpenAI Responses API。

不要將金鑰放在檔案、Issue、聊天或 workflow input。GitHub Secrets 無法讀回明文；有設定也仍需實際執行確認有效。可選 repository variable `OPENAI_MODEL`，預設 `gpt-4.1-mini`。

本次 PR 分支推送已觸發 smoke；後續請手動執行 smoke（每來源最多 2 筆、AI 最多 2 篇；每平台選最新含附件貼文，至少一篇須實際完成圖片判讀）；也可到 **Actions → Social update (bounded) → Run workflow → mode=smoke**。只有兩平台都有合格資料、兩次 AI 成功且實際圖片判讀成功，才將 `social_validation.json.passed` 設為 true。未成功，排程不做付費抓取。

目前已移除 workflow 的 schedule 觸發器，PR 保持未合併。即使 smoke 通過也不會自動開始每日抓取；待確認判讀品質與費用後，再明確啟用排程。所有付費操作只接受手動 workflow_dispatch，缺少 OPENAI_API_KEY 時會在任何付費 API 前停止。

## 歷史判讀與費用

不重新抓取已上傳的整段歷史。先 smoke，再手動 `mode=classify-only`、`ai_limit=50` 分批清空歷史 pending。每次最多 50 篇，預設手動 2 篇；每日自動 10 篇也會繼續處理 backlog。`social_report.json` 顯示待處理數、成功產生訊號數；retry 不當成已完成，後續可重試。

每月最多預留 70 次 Actor run、預設 400 次 AI 嘗試。歷史 659 篇若需在同月完成，可將 repository variable `MONTHLY_AI_LIMIT` 暫設 `1000`（允許 1..2000），完成後調回 `400`；預設不會為了補歷史自動突破預算。預算先寫入 `usage.json`，中斷也不退回預留值。每個 Actor 指定 180 秒、512 MB、`maxItems` 及 `maxTotalChargeUsd=0.10`。兩平台成功 run 的 PPE 上限合計每月約 US$7；這不是 Apify 帳單保證，部分非 PPE 費用、方案訂閱或供應商規則不一定受此參數約束。另在 Apify Console 設帳戶預算／通知。OpenAI 另計費；每篇限制輸出 token、圖片張數／尺寸，請在 OpenAI 專案設 quota 和預算警示。嘗試次數上限不是固定美元上限。

抓取採已完成時間窗加 2 天重疊，依來源 ID 去重。若回傳數達上限，保留時間窗，下一次向較舊資料分頁，不將游標跳到最新而漏中間資料。相同秒數太多造成分頁無進展會停下等待檢查。來源失敗分開記錄，不前進該來源游標。資料量上限與 scraper 本身限制仍可能影響完整性，應定期核對來源。

`acquisition.json` 保存 run ID；GET 可重試，啟動付費 POST 不盲目重送。若出現 `submission_uncertain=true`，至 Apify Console 找出對應 run，將 run_id 設回狀態檔並把 uncertain 改 false；若確認沒有啟動才清除 uncertain。失敗 run 亦需先檢查 Console；要重新付費重跑，清除該來源 run_id，保留時間窗。workflow 即使失敗也提交狀態；若提交或推送失敗，從該 run artifact／log 與 Apify Console 核對，勿直接重跑付費抓取。

## TradingView 手動更新

GitHub 更新**不會**自動同步到 TradingView。

1. 在 Actions 下載 `social-update` artifact 的完整 `8zz-indicator.pine`，或開啟 GitHub 最新檔案的 Raw 內容。
2. TradingView → Pine Editor，備份原腳本，再用完整檔案取代編輯器內容。
3. 儲存、加入圖表／更新圖表，檢查 Pine 編譯及事件標籤。
4. 既有提醒使用建立時的腳本快照，需要刪除並重建提醒才能套用新腳本。

## 績效及驗證限制

Mode A 與 Mode B 都依 `direction × 價格變動`，正數勝、負數敗、零持平，做多下跌也計敗。勝率分母為已平倉非零交易，不混入 open／unknown。無新行情時使用快取重建，`docs/events.json.market_data_mode` 標示快取，不能當作最新行情績效。可安裝 scripts/requirements.txt 後執行 `python scripts/build_site_data.py` 刷新行情；外部行情可用性另行驗證。

離線驗證：`python -m unittest discover -s scripts -p 'test*.py' -v`；`python scripts/social_pipeline.py` 可無金鑰重建完整 Pine；`python scripts/build_site_data.py --offline` 使用快取。Pine 編譯須在 TradingView 驗證，本環境沒有 Pine 編譯器。

## 官方介面核對（2026-11-06）

- [Facebook Actor OpenAPI](https://apify.com/apify/facebook-posts-scraper/api/openapi)：startUrls、resultsLimit、onlyPostsNewerThan、onlyPostsOlderThan，移除舊 parse-all 假設。
- [Threads Actor 作者文件](https://apify.com/automation-lab/threads-scraper)：mode=posts、usernames、maxPosts、postedAfter、postedBefore、includeProfile=false；每列仍嚴格驗證 isReply=false 且 isRepost=false。
- [Apify Run Actor](https://docs.apify.com/api/v2/actors-runs-post)：非同步 run、maxItems、maxTotalChargeUsd；先保存 ID 再輪詢、讀取 dataset。
- [Responses API](https://platform.openai.com/docs/api-reference/responses)、[Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)、[Images and vision](https://platform.openai.com/docs/guides/images-vision)、[GPT-4.1 mini](https://platform.openai.com/docs/models/gpt-4.1-mini)：使用 POST /v1/responses、input_text/input_image、text.format 嚴格 JSON Schema；不再使用 Google 的 AI SDK 或 API。
- [Requests](https://pypi.org/project/requests/)、[yfinance](https://pypi.org/project/yfinance/)：僅行情刷新才需要第三方依賴；抓取與判讀流程使用 Python 標準函式庫。

## OpenAI 遷移後的設定與驗證順序

原實作確實呼叫 Google generateContent；現在程式改為 OpenAI Responses API，沒有舊供應商 fallback。必要 AI Secret 僅 OPENAI_API_KEY，APIFY_TOKEN 沿用。無須設定 GOOGLE_API_KEY。

1. 在 OpenAI API 專案建立金鑰，確認 API 額度與模型權限；ChatGPT 訂閱不等於 API 額度。
2. GitHub 本儲存庫 → Settings → Secrets and variables → Actions → New repository secret → 名稱 `OPENAI_API_KEY`，貼入金鑰後儲存；不要貼在聊天、Issue 或 workflow input。
3. 可選 variable `OPENAI_MODEL`，預設 `gpt-4.1-mini`；替換模型須支援 Responses、圖片輸入及嚴格結構化輸出。更換模型後必須重做 smoke，舊結果不可解鎖新模型批次。
4. 手動選 PR 分支執行 mode=smoke，每來源最多 2 篇、AI 最多 2 次。檢查判讀理由、圖片實際傳入、引用界線與標的，並核對 validation 的 usage（input_tokens、output_tokens）和 OpenAI 專案用量帳單。Token 數不是美元帳單；月嘗試數限制也不是美元保證。
5. smoke 通過且品質與費用可接受，才以 classify-only 分批處理 659 篇；每次上限 50。PR 仍不自動合併、排程仍關閉。

固定輸出包含 direction（-1/0/1）、strength（1..3）、target、ticker、reason、investment_related、clear、images_reviewed、author_commentary、quoted_summary。標的不確定或情緒模糊時不發訊號，保留 review 待確認；HTTP 錯誤、拒答、輸出不完整、格式無效或圖片無法讀取則保留 retry。每篇保存 provider、model、prompt_version、response_id 與 token usage，不保存金鑰或 API 原始錯誤。

## 目前階段：品質驗證，線上仍停用

技術 smoke 完成不解除暫停。上述線上操作順序僅供未來另行授權時參考，現在不執行。最新狀態分流與標的證據規則以 [離線語意檢查](SEMANTIC_QUALITY.md) 為準：確定無關／中性為 no_signal，資訊不足／矛盾為 review，只有技術失敗為 retry。no_signal 與 review 不會在一般流程自動再次送 API；穩定的輸入／附件問題也須人工補正。完整模型答案留在 model_candidate，正式欄位可因缺證據被清空或方向歸零。

請先確認 [10篇品質候選](QUALITY_SAMPLES.md)，未確認前不做小批生成，亦不批次、排程、Pages或合併。圖片 OCR 僅為未驗證的來源資料，不能當作人工已看圖。
