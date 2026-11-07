# 下一階段批次操作方案（僅準備，尚未授權／啟用）

本輪沒有處理其餘歷史、沒有生成或新增樣本。`plan_quality_batch.py` 是**純離線規劃器與停止判斷函式**，沒有API客戶端、金鑰存取或執行器；既有ChatAnywhere批次仍被禁止，不能直接以舊的run_social_update.py／解除pause去跑。不得把這份方案視為批次授權。

## 建議流程

1. 先審核 [現有重驗結果](QUALITY_RULE_REVIEW.md)，接受待確認的處置方式、影片未分析限制與新規則版本。候選不是gold；若要以新prompt重測，另明列篇目與次數，不自動重送。
2. 日後另行授權時，只選**明確指定、未判讀的新資料**，建立清單。每筆含key、content_hash及status=unprocessed；已可接受、待確認、技術失敗或已預留的資料不自動進隊列。資料編輯須保留舊紀錄及新hash，不能為換答案假裝改內容。
3. 離線產生計畫，檢視實際選取ID及筆數。例如：

   ```bash
   python scripts/plan_quality_batch.py --state-file selected-new-records.json --out /tmp/next-batch.json --limit 5 --monthly-remaining 50
   ```

   上述檔案只是未來明確選取清單的檔名範例，本輪未建立或讀取其他歷史清單。這個命令只產生計畫，不執行API。monthly-remaining是**自行設定的剩餘嘗試數預算**，50僅為保守起始範例，不是供應商實際點數或免費保證。
4. 確認帳號仍為允許的免費模型、實際可用額度及用途限制，再另行授權該批。若無法確認免費額度，預設不開跑，不把未知當零扣點或視為有餘額。
5. 另行接上受限的一次性Actions worker，固定新規則／schema／輸入digest。金鑰僅CHATANYWHERE_API_KEY，接入點.tech/v1、gpt-5-mini／minimal；不載入官方金鑰、不切付費服務。候選答案不進prompt，上下文預設同篇；任何新增先前貼文都須記錄來源與發文時間，不得晚於主貼文。
6. **先持久保存預留帳本，成功後才注入AI Secret並發送**。每批及post@content_hash都唯一；同一concurrency group，使用預期GitHub ref／SHA拒絕競態。`reserve()`只提供預留草案；後續worker必須把它真正保存至遠端並核對成功，不能只存在runner記憶體或等到最後才上傳artifact。
7. 逐筆保存原回應／安全用量、媒體hash與獨立規則結果。持倉／提及／報價分組，影片文字限定明示；結果仍先存品質紀錄，人工驗收後才另行決定正式Pine更新，不自動發布或合併。

## 上限與費用停止

- 預設每批 **5次生成**，硬上限 **10次**；每篇最多一次，max_output_tokens=3000。無自動重試，無跨供應商備援。
- 月嘗試預算先由使用者設定；`reserve()`會扣除剩餘預留數，跨批不能重複花用。月度重置需明確的新帳本週期，仍保留已嘗試post@hash，不能靠換batch ID重送。
- crash時預留視為已消耗、狀態不明，不自動重播；查核已保存回應／服務用量後，技術失敗重送也必須另行授權。
- HTTP402／429、insufficient_quota／billing_hard_limit_reached／rate_limit_exceeded、任何其他API／傳輸異常、固定格式／必要功能不符：保存當前進度後立即停止，不做下一筆。
- 若服務回報剩餘免費點數或請求數<=0，停止；回報欄位異常也停止。未回傳額度是未知，不是零扣點，更不是可任意繼續；是否開跑前仍需確認免費額度與授權預算。
- 數量／output上限**不是**完整token、點數或金額硬上限，圖片與輸入token會變動。只記服務回報實際usage及可取得的點數，不從token推算點數。

## 已準備與尚未完成

已提供：離線manifest篩選與5／10上限、重複／crash預留禁止、月預算扣減及額度／API／格式停止判斷，並有離線測試。

尚未接通：新批次線上worker、遠端預留帳本寫入／CAS、真實額度查核與新規則線上驗證。**這些不在本輪執行**，不可宣稱現有排程已會替新規則安全批次。舊smoke／continuation的授權已消耗、仍停用，不能重新使用。

免費版個人交易研究是否允許仍未確認，不推定可供客戶或商業服務。TradingView不會隨GitHub自動同步；正式驗收並另行批准更新後，仍需手動複製完整Pine、儲存、更新圖表及必要提醒。
