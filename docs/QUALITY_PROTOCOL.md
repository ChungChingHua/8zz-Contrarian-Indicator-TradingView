# 品質測試固定規則與授權（執行前凍結）

使用者已授權原10篇、每篇最多一次、合計最多10次生成；無自動重試，不查模型清單或未確認的餘額接口。僅 CHATANYWHERE_API_KEY，接入點 https://api.chatanywhere.tech/v1，請求 gpt-5-mini / minimal / Responses API / strict JSON schema / store=false / 無工具；不換模型、付費服務或官方金鑰。模型／推理 metadata 只列服務回報，未獨立驗證。

## 三軸獨立

1. 投資相關性：investment / unrelated / insufficient_information，另給理由。
2. 情緒：panic / euphoria / neutral / mixed / insufficient_information，另給強度1..3及逐字證據。方向是投資情緒的反向方向：投資恐慌／痛苦 +1，投資亢奮 -1，其他0。缺標的、缺代碼不能使已明確的情緒方向歸零。
3. 標的辨識：名稱、代碼、本人立場／僅持倉／僅提及／不確定及證據分開。可留空；圖片候選綁定實際附圖索引與SHA-256，標 pending_human_confirmation，不宣稱人工核圖。

正式主線的 semantic gate 亦修正為 target_issues 獨立於情緒，目標不明不再是情緒歸零原因。舊文件凡宣稱「標的不明必須方向0」均由本文件取代。第7篇原文對投資痛苦已有明確證據，重新提出候選 +1／強度3／標的空白；這是人工候選，**不送入待測模型，也不是標準答案**。

## 盲測與時間限制

- 固定規則與 schema：scripts/quality_protocol.py。protocol SHA-256：`a1fa9e748994ac713a05bf0633f3b152bca0a86c325e268534456046faab5846`。
- 輸入清單：data/quality_test_plan.json。canonical plan SHA-256：`c300306ddaaad7c6cf6c5008042e2d34cf8f7f62e944d948777e5cfa8d6493de`。runner 與 workflow 再核對兩個 digest，規則／輸入改變即拒絕執行。
- 模型只收該篇原文、發文時間、既有第三方引用文字（如有）與實際附圖。**本輪不用任何先前或之後貼文，context=[]**，不讀市場價格快取／後續行情或留言。若未來另加先前貼文，必須新增可驗證來源與發布時間且不晚於主貼文，重新凍結規則與授權；本輪不增加。
- 不送 category、proposed、acceptable_decisions、候選分類、原有 analysis 或平台 OCR；payload 使用明確白名單。產生後才在離線報告比對，不能回灌答案或為貼合候選而重送。
- 候選並非 gold：原提案另外保留 data/quality_original_proposals.json；修正後提案見 data/quality_samples.json。使用者只同意使用這10篇，不代表每個候選答案正確。
- 只有抓取時的既有原文／媒體快照，無法獨立證明較早貼文是否曾編輯；不補用後來內容來修正情緒。

## 舊回應是否重用

既有兩筆來自舊 prompt／schema，當時將標的不明與 clear 混用，缺少此輪獨立相關性、情緒、圖中文字與標的證據欄位。Facebook 更無完整原始回應，故不符合「同規則且資料完整」條件；不得把舊答案包裝成新規則成功。此次最多新增10次，不重用這兩筆為本輪答案。

## 範圍與失敗

一般 pause=true 不變；只在一次性 runner 記憶體中開放固定10篇的媒體讀取。歷史 archive 只讀，用於還原既有帶簽名媒體連結；不把簽名 URL 或儲存庫檔案送給模型／公開新產物。每篇實際附圖齊全後才發出唯一生成請求，不降級為純文字。

API／額度／格式／必要功能或媒體異常立即保存並停止，已嘗試樣本為 retry 或 input_review，其餘 not_attempted，不標完成、不重試。每個生成與媒體HTTP嘗試都在網路前記帳；workflow run_attempt=1、scope、consumed報告及固定並行鎖防止重複執行。成功僅標 evaluated_test_only，不寫 social_posts.json、Pine 或正式驗證解鎖檔。

產物只含安全測試紀錄。token、模型／推理回報與前後額度標頭分列；查不到點數、剩餘請求額度或實際扣點就標未知，不以tokens推算點數，也不宣稱零扣點。不查未經確認的點數接口。

執行後關閉一次性入口，維持無批次、無排程、無Pages、PR不合併；個人交易研究的免費版用途限制仍未確認，不推定客戶或商用可用。

離線測試：89項通過，包含十篇各一次、拒絕重跑／額度錯誤立即停止、禁止純文字降級、候選與未來上下文不進prompt、schema／推理／工具輸出驗證、秘密反射遮蔽、獨立情緒與標的及圖片候選未人工核實標示。

## 非服務異常的輸入阻擋處置

前4篇均HTTP200及schema有效，第5篇實際是Video，在任何生成前被拒。這不是API、額度或供應商異常；不把影片縮圖冒充完整影片，也不送純文字。保存第5篇input_review後，只以同一prompt/schema、同一10次上限處理原本未嘗試的第6～10篇，前4篇重用且不重送、第5篇不重試。專用continuation僅接受此確切4成功＋1已知Video阻擋＋5未嘗試狀態，若任何先前API錯誤、已嘗試或再次執行即拒絕。這不是對失敗生成的重試，也不變更已凍結規則。最終須如實列第5篇沒有模型答案，不能聲稱10篇全部完成。
