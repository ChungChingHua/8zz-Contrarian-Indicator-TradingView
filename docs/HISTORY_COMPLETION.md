# 一次性歷史補齊執行紀錄

本次因實際阻塞停止，**尚未補齊全部歷史判讀**。

資料抓取截止 UTC 2026-11-14T10:21:07.585530+00:00（Asia/Taipei 為 2026-11-14T18:21:07.585530+08:00）；共 710 篇。已走訪至 2026-11-05T01:23:43+08:00，其中待確認／失敗另列；本輪最後有效回應 2026-11-12T21:59:30+08:00，最新事件 2026-11-12T13:48:28+08:00。

完整 Pine 398 事件 = 原歷史 151 + 累計新增 247；其中此歷史 scope 累計新增 242。本次續跑新增 18。

狀態依來源貼文計：有訊號 249、無訊號 321、待確認 102、失敗 21、狀態不明 0、尚未處理 17（去重後 17 組）。跨平台同組會對應多筆貼文，但只產生一個事件。

本 scope 累計生成 HTTP 656 次，成功固定格式回應 640；7 筆 HTTP 回應無 usage，不假定其零 tokens。已回報用量輸入 1873697／輸出 103062／合計 1976759 tokens。實際點數扣除未知；即時免費請求／點數餘額與重設時刻若無服務回傳即為未知，先前阻塞保留於 control.blocker_history。

原始程式曾未處理 429 的 usage=null，導致最後彙整步驟失敗；已修正並以全部已保存回應離線重建，不新增任何生成。供應商錯誤原含遮蔽後的金鑰識別片段，最新帳本已進一步去除該片段，保留清理前 JSON hash；完整金鑰未輸出。

歷史基準已依使用者提供的原作者65事件版本校正為151筆：保留未改寫的Fork150事件來源檔，補回3/31缺漏1筆，另外5筆欄位校正及1筆明確校時均有差異紀錄。圖表採校正後基準；不是宣稱Fork150筆在輸出中逐字不變。詳見 docs/PINE_AUTHOR_HISTORY_FIX.md 與 data/author_history_reconciliation_audit.json。

```json
{
  "scope": "history-completion-20261107",
  "cutoff_utc": "2026-11-14T10:21:07.585530+00:00",
  "cutoff_taipei": "2026-11-14T18:21:07.585530+08:00",
  "acquisition_completed": true,
  "archive_posts": 710,
  "data_range_by_source": {
    "facebook": {
      "first": "2026-07-20T08:32:36+08:00",
      "latest_post": "2026-11-13T23:21:14+08:00"
    },
    "threads": {
      "first": "2026-07-20T13:02:00+08:00",
      "latest_post": "2026-11-14T10:54:32+08:00"
    }
  },
  "post_status_counts": {
    "completed_signal": 249,
    "completed_no_signal": 321,
    "pending_confirmation": 102,
    "technical_failure": 14,
    "input_failure": 7,
    "not_started": 17,
    "unknown": 0
  },
  "remaining_not_started_groups": 17,
  "remaining_not_started_platform_posts": 17,
  "latest_attempted_or_reviewed_date": "2026-11-13T00:56:41+08:00",
  "all_posts_visited_before_first_unstarted": "2026-11-05T01:23:43+08:00",
  "successfully_completed_contiguous_prefix": "2026-07-20T18:41:00+08:00",
  "first_unstarted_date": "2026-11-05T03:04:10+08:00",
  "latest_signal_date": "2026-11-12T13:48:28+08:00",
  "pine": {
    "historical_events": 151,
    "added_events": 247,
    "total_events": 398,
    "same_bar_policy": "latest_post_before_filters",
    "historical_blocks_preserved": true,
    "historical_basis": "reconciled_published_author_history",
    "fork_base_events": 150,
    "author_reference_events": 65,
    "historical_reference_changes": {
      "updated_events": 5,
      "retimed_events": 1,
      "inserted_events": 1,
      "unchanged_fork_events": 144
    },
    "archived_fork_source_unchanged": true,
    "fork_base_literals_preserved": false,
    "historical_neutral_events_preserved": 0,
    "new_events_nonzero": true,
    "arrays_paired": true,
    "timestamps_ordered": true,
    "directions_strengths_valid": true,
    "tradingview_compiled": false,
    "initialization_functions": 20,
    "max_events_per_function": 20,
    "first_bar_calls": 20,
    "event_initialization_chunk_limit": 20,
    "event_encoding": "packed-v1",
    "packed_event_round_trip": true,
    "max_payload_bytes": 10249,
    "payload_byte_limit": 30000,
    "executable_array_push_statements": 5,
    "il_tokens_measured": false
  },
  "last_new_valid_response_date": "2026-11-12T21:59:30+08:00",
  "new_stop_post_date": "2026-11-13T00:56:41+08:00",
  "new_generation_attempts": 656,
  "new_http_responses": 656,
  "new_status_counts": {
    "pending_confirmation": 89,
    "completed_no_signal": 313,
    "completed_signal": 242,
    "technical_failure": 12,
    "input_failure": 7
  },
  "service_reported_usage": {
    "input_tokens": 1873697,
    "output_tokens": 103062,
    "total_tokens": 1976759,
    "reasoning_tokens": 0
  },
  "new_validated_responses": 640,
  "images_attached": 459,
  "videos_unanalysed": 79,
  "http_responses_without_usage": 7,
  "service_reported_cached_input_tokens": 1289600,
  "apify_http_counts": {
    "GET": 13,
    "POST": 2
  },
  "apify_runs": [
    {
      "source": "facebook",
      "run_id": "1eDyx3uOHnTVfD5Ln",
      "status": "SUCCEEDED",
      "counts": {
        "fetched": 20,
        "accepted": 20,
        "new": 20,
        "overlap": 0,
        "excluded": {}
      },
      "reported_cost": {
        "usageTotalUsd": 0.127
      },
      "http_status": null
    },
    {
      "source": "threads",
      "run_id": "hinVUOAgNEM17Le6K",
      "status": "SUCCEEDED",
      "counts": {
        "fetched": 27,
        "accepted": 24,
        "new": 24,
        "overlap": 0,
        "excluded": {
          "reply_repost_or_unknown": 3
        }
      },
      "reported_cost": {
        "usageTotalUsd": 0
      },
      "http_status": null
    }
  ],
  "model_queries": 0,
  "other_ai_provider_queries": 0,
  "actual_points_deducted": null,
  "quota_headers": {},
  "stop_reason": "provider_access_quota_or_common_failure",
  "service_quota_statement": null,
  "all_history_fully_classified": false,
  "rule_sha256": "8ccd8bbe6388705261e7240897417683f2dc6e2016f5db9d5eca462533837162",
  "provider_model_and_reasoning": "Service-reported gpt-5-mini / minimal, not independently verified",
  "usage_tracking_note": "ChatAnywhere request accounting is from durable ledgers; legacy usage.json ai_attempts is not the cumulative ChatAnywhere total.",
  "accounting_note": "Post counts include all prior tests, failures, reviews and cross-platform members; Pine counts are events, not posts. Tokens are service reports, not points or verified bills.",
  "current_session": {
    "id": "20261114-media-repair-04",
    "generation_attempts": 37,
    "validated_responses": 36,
    "added_events": 18,
    "pine_count_delta_since_session": 18,
    "historical_reference_event_delta_since_session": 0,
    "service_reported_usage": {
      "input_tokens": 98847,
      "output_tokens": 5751,
      "total_tokens": 104598,
      "reasoning_tokens": 0
    },
    "status_counts": {
      "completed_no_signal": 15,
      "completed_signal": 18,
      "input_failure": 0,
      "pending_confirmation": 3,
      "technical_failure": 1
    },
    "actor_runs_started": 0,
    "saved_dataset_get_requests": 0,
    "actual_points_deducted": null,
    "run_url": "https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/43585240072",
    "stop_http_status": null,
    "status_count_transitions": {
      "completed_no_signal": 15,
      "completed_signal": 18,
      "input_failure": 0,
      "pending_confirmation": 3,
      "technical_failure": 1
    },
    "recovered_zero_generation_inputs": 0
  }
}
```

原作者規則與 SHA256 未變。以前測試資料不是目前原作者標準的已完成結果；全部列入 inventory，未重送，也不自動沿用舊的額外門檻。舊帳本輸出矛盾的 technical_failure 僅在彙整清單標為待確認，原回應與原帳本不改。

資料涵蓋截止時間請看 acquisition_completed、cutoff_utc 及 control 內各來源完成窗；latest_post 只代表最新抓到的貼文。latest_attempted_or_reviewed_date 包含以前測試樣本，不能當作連續處理進度。all_posts_visited_before_first_unstarted 包含待確認／失敗的已走訪資料，並非全部判讀成功；完整成功的前綴另列 successfully_completed_contiguous_prefix。最新訊號日期也不能代替資料處理完成日期。

每篇來源、時間、狀態、原始帳本及原因見 data/history_completion_inventory.json。原文保留在 archive／增量資料，原始模型回應與 processed 分別保存於 history_progress。

固定使用免費金鑰、.tech/v1、gpt-5-mini、minimal、嚴格格式；模型與推理僅供應商回報。圖片只有實際下載並附入者才標為讀取；影片未分析，圖片下載失敗及技術問題如實記錄。

單篇矛盾保留待確認；單篇格式／媒體失敗隔離，不產生訊號或自動重試。連續三篇技術問題觸發共同故障停止（僅操作保護，不是情緒規則）；額度、認證、存取、服務端錯誤或已送出未保存的未知狀態立即保存停止。

前後免費點數及實際扣點若未由服務回傳就是未知，不等同零，也不能由 tokens 換算。Apify 每 run 保留180秒／512MB／maxItems 50及禁止自動重啟；依使用者最新指示不設程式單次費用上限或每月啟動次數上限，啟動與費用仍記帳，服務端額度／認證／截斷異常仍保存停止；run回報費用不是獨立結算帳單。

成對完整 Pine：candidates/8zz-history-latest.pine（指標）、candidates/8zz-strategy-latest.pine（策略），同版資訊見 candidates/8zz-pine-delivery.json。兩份保留相同全部事件、作者署名及 MPL-2.0；待確認／技術失敗／unknown 無新增箭頭。使用者已確認前一候選可載入，這份新生成檔未在 TradingView 實際編譯。手動下載全文至 Pine Editor 完整取代、儲存並更新圖表，GitHub 不會自動同步。

恢復方式：先核對 control 與各帳本；已完成、待確認、失敗、unknown 不自動重送。unknown 須人工查明原請求；quota／access 故障修復後，只續尚未送出項目，重新取得同一已保存 Apify dataset 不會重新啟動 Actor。新執行必須保留同一截止時間與 scope；不得重新抓整段歷史。

下一筆尚未處理日期為 2026-11-05T03:04:10+08:00（Asia/Taipei）。資料 cutoff 維持不變，恢復媒體只讀既有 dataset，不另啟動 Actor。每次續跑將先前阻塞與基準用量保留在 control，只有本次明確授權的入口才能繼續；完成、待確認、失敗與 unknown 不自動重送。

本次 API 次數僅指 AI 生成及 Apify 啟動／讀取；GitHub 進度保存與圖片下載另計，沒有把上述數字宣稱為全部 HTTP 流量。data/usage.json 的 ai_attempts 為舊流程計數，不等於 ChatAnywhere 全部呼叫量，應以本次及既有帳本查核。

只做一次性執行，不啟用持續排程、不發布 Pages、不合併 PR。
