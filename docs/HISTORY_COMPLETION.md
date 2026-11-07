# 一次性歷史補齊執行紀錄

本次因實際阻塞停止，**尚未補齊全部歷史判讀**。

資料抓取截止 UTC 2026-11-07T12:15:59.578797+00:00（Asia/Taipei 為 2026-11-07T20:15:59.578797+08:00）；共 666 篇。已走訪至 2026-08-04T18:41:55+08:00，其中待確認／失敗另列；本輪最後有效回應 2026-08-04T10:33:34+08:00，最新事件 2026-08-03T13:50:30+08:00。

完整 Pine 187 事件 = 原歷史 150 + 累計新增 37；其中本輪新增 32。

狀態依來源貼文計：有訊號 38、無訊號 41、待確認 24、失敗 3、狀態不明 0、尚未處理 560（去重後 555 組）。跨平台同組會對應多筆貼文，但只產生一個事件。

本輪生成 HTTP 81 次，成功固定格式回應 80；1 筆 HTTP 回應無 usage，不假定其零 tokens。已回報用量輸入 230264／輸出 11747／合計 242011 tokens。實際點數扣除未知；服務宣告共用 100 次免費請求的 24 小時視窗已耗盡，沒有提供確切重設時刻。

原始程式曾未處理 429 的 usage=null，導致最後彙整步驟失敗；已修正並以全部已保存回應離線重建，不新增任何生成。供應商錯誤原含遮蔽後的金鑰識別片段，最新帳本已進一步去除該片段，保留清理前 JSON hash；完整金鑰未輸出。

```json
{
  "scope": "history-completion-20261107",
  "cutoff_utc": "2026-11-07T12:15:59.578797+00:00",
  "cutoff_taipei": "2026-11-07T20:15:59.578797+08:00",
  "acquisition_completed": true,
  "archive_posts": 666,
  "data_range_by_source": {
    "facebook": {
      "first": "2026-07-20T08:32:36+08:00",
      "latest_post": "2026-11-07T17:08:22+08:00"
    },
    "threads": {
      "first": "2026-07-20T13:02:00+08:00",
      "latest_post": "2026-11-07T17:09:34+08:00"
    }
  },
  "post_status_counts": {
    "completed_signal": 38,
    "completed_no_signal": 41,
    "pending_confirmation": 24,
    "technical_failure": 3,
    "not_started": 560,
    "input_failure": 0,
    "unknown": 0
  },
  "remaining_not_started_groups": 555,
  "remaining_not_started_platform_posts": 560,
  "latest_attempted_or_reviewed_date": "2026-11-06T22:07:49+08:00",
  "all_posts_visited_before_first_unstarted": "2026-08-04T18:41:55+08:00",
  "successfully_completed_contiguous_prefix": "2026-07-20T18:41:00+08:00",
  "first_unstarted_date": "2026-08-04T21:18:23+08:00",
  "latest_signal_date": "2026-08-03T13:50:30+08:00",
  "pine": {
    "historical_events": 150,
    "added_events": 37,
    "total_events": 187,
    "historical_blocks_preserved": true,
    "historical_neutral_events_preserved": 1,
    "new_events_nonzero": true,
    "arrays_paired": true,
    "timestamps_ordered": true,
    "directions_strengths_valid": true,
    "tradingview_compiled": false,
    "initialization_functions": 10,
    "max_events_per_function": 20,
    "first_bar_calls": 10,
    "event_initialization_chunk_limit": 20
  },
  "last_new_valid_response_date": "2026-08-04T10:33:34+08:00",
  "new_stop_post_date": "2026-08-04T18:41:55+08:00",
  "new_generation_attempts": 81,
  "new_http_responses": 81,
  "new_status_counts": {
    "pending_confirmation": 12,
    "completed_no_signal": 36,
    "completed_signal": 32,
    "technical_failure": 1
  },
  "service_reported_usage": {
    "input_tokens": 230264,
    "output_tokens": 11747,
    "total_tokens": 242011,
    "reasoning_tokens": 0
  },
  "new_validated_responses": 80,
  "images_attached": 57,
  "videos_unanalysed": 13,
  "http_responses_without_usage": 1,
  "service_reported_cached_input_tokens": 168448,
  "apify_http_counts": {
    "GET": 18,
    "POST": 2
  },
  "apify_runs": [
    {
      "source": "facebook",
      "run_id": "TQsq3MaaGMBqd77i0",
      "status": "SUCCEEDED",
      "counts": {
        "fetched": 5,
        "accepted": 5,
        "new": 4,
        "overlap": 1,
        "excluded": {}
      },
      "reported_cost": {
        "usageTotalUsd": 0.022
      },
      "http_status": null
    },
    {
      "source": "threads",
      "run_id": "mGp428lwhhYyYDGPQ",
      "status": "SUCCEEDED",
      "counts": {
        "fetched": 6,
        "accepted": 4,
        "new": 3,
        "overlap": 1,
        "excluded": {
          "reply_repost_or_unknown": 2
        }
      },
      "reported_cost": {
        "usageTotalUsd": 0.02
      },
      "http_status": null
    }
  ],
  "model_queries": 0,
  "other_ai_provider_queries": 0,
  "actual_points_deducted": null,
  "quota_headers": {},
  "stop_reason": "provider_access_quota_or_common_failure",
  "service_quota_statement": {
    "http_status": 429,
    "source": "service error response",
    "shared_free_requests_per_24h_window": 100,
    "remaining_free_requests": "exhausted, service statement only",
    "actual_points_deducted": null,
    "reset_time": null,
    "note": "No paid upgrade, no retry, no alternative key/provider/model. The 429 response reports no token usage."
  },
  "all_history_fully_classified": false,
  "rule_sha256": "8ccd8bbe6388705261e7240897417683f2dc6e2016f5db9d5eca462533837162",
  "provider_model_and_reasoning": "Service-reported gpt-5-mini / minimal, not independently verified",
  "usage_tracking_note": "ChatAnywhere request accounting is from durable ledgers; legacy usage.json ai_attempts is not the cumulative ChatAnywhere total.",
  "accounting_note": "Post counts include all prior tests, failures, reviews and cross-platform members; Pine counts are events, not posts. Tokens are service reports, not points or verified bills."
}
```

原作者規則與 SHA256 未變。以前測試資料不是目前原作者標準的已完成結果；全部列入 inventory，未重送，也不自動沿用舊的額外門檻。舊帳本輸出矛盾的 technical_failure 僅在彙整清單標為待確認，原回應與原帳本不改。

資料涵蓋截止時間請看 acquisition_completed、cutoff_utc 及 control 內各來源完成窗；latest_post 只代表最新抓到的貼文。latest_attempted_or_reviewed_date 包含以前測試樣本，不能當作連續處理進度。all_posts_visited_before_first_unstarted 包含待確認／失敗的已走訪資料，並非全部判讀成功；完整成功的前綴另列 successfully_completed_contiguous_prefix。最新訊號日期也不能代替資料處理完成日期。

每篇來源、時間、狀態、原始帳本及原因見 data/history_completion_inventory.json。原文保留在 archive／增量資料，原始模型回應與 processed 分別保存於 history_progress。

固定使用免費金鑰、.tech/v1、gpt-5-mini、minimal、嚴格格式；模型與推理僅供應商回報。圖片只有實際下載並附入者才標為讀取；影片未分析，圖片下載失敗及技術問題如實記錄。

單篇矛盾保留待確認；單篇格式／媒體失敗隔離，不產生訊號或自動重試。連續三篇技術問題觸發共同故障停止（僅操作保護，不是情緒規則）；額度、認證、存取、服務端錯誤或已送出未保存的未知狀態立即保存停止。

前後免費點數及實際扣點若未由服務回傳就是未知，不等同零，也不能由 tokens 換算。Apify 維持每 run 180 秒／512MB／maxItems 50／maxTotalChargeUsd 0.10、每月70次；run 回報費用不一定等同完整帳單，未儲值或提高上限。

候選完整 Pine：candidates/8zz-history-latest.pine，保留所有原始歷史事件、作者署名及 MPL-2.0；待確認／技術失敗／unknown 無新增箭頭。使用者已確認前一候選可載入，這份新生成檔未在 TradingView 實際編譯。手動下載全文至 Pine Editor 完整取代、儲存並更新圖表，GitHub 不會自動同步。

恢復方式：先核對 control 與各帳本；已完成、待確認、失敗、unknown 不自動重送。unknown 須人工查明原請求；quota／access 故障修復後，只續尚未送出項目，重新取得同一已保存 Apify dataset 不會重新啟動 Actor。新執行必須保留同一截止時間與 scope；不得重新抓整段歷史。

本輪可接續的第一篇是 Threads 3956314846774104604，2026-08-04 21:18:23（Asia/Taipei）。額度重設時間未取得，不能假定台灣午夜恢復。恢復後保留現有資料 cutoff，不另啟動 Apify；若需要恢復新資料的私有媒體網址，只讀已保存 dataset。先將本次阻塞保留於 control 的歷史紀錄，明確解除 closed／stop_reason，再啟用這個一次性手動入口；只選 not_started，這次 429 失敗資料也不自動重送。

本次 API 次數僅指 AI 生成及 Apify 啟動／讀取；GitHub 進度保存與圖片下載另計，沒有把上述數字宣稱為全部 HTTP 流量。data/usage.json 的 ai_attempts 為舊流程計數，不等於 ChatAnywhere 全部呼叫量，應以本次及既有帳本查核。

只做一次性執行，不啟用持續排程、不發布 Pages、不合併 PR。
