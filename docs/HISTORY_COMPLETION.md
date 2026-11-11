# 一次性歷史補齊執行紀錄

本次因實際阻塞停止，**尚未補齊全部歷史判讀**。

資料抓取截止 UTC 2026-11-07T12:15:59.578797+00:00（Asia/Taipei 為 2026-11-07T20:15:59.578797+08:00）；共 666 篇。已走訪至 2026-09-23T10:02:01+08:00，其中待確認／失敗另列；本輪最後有效回應 2026-09-23T08:59:55+08:00，最新事件 2026-09-22T18:54:02+08:00。

完整 Pine 294 事件 = 原歷史 151 + 累計新增 143；其中此歷史 scope 累計新增 138。本次續跑新增 0。

狀態依來源貼文計：有訊號 145、無訊號 191、待確認 71、失敗 12、狀態不明 0、尚未處理 247（去重後 247 組）。跨平台同組會對應多筆貼文，但只產生一個事件。

本 scope 累計生成 HTTP 385 次，成功固定格式回應 375；4 筆 HTTP 回應無 usage，不假定其零 tokens。已回報用量輸入 1094612／輸出 58849／合計 1153461 tokens。實際點數扣除未知；即時免費請求／點數餘額與重設時刻若無服務回傳即為未知，先前阻塞保留於 control.blocker_history。

原始程式曾未處理 429 的 usage=null，導致最後彙整步驟失敗；已修正並以全部已保存回應離線重建，不新增任何生成。供應商錯誤原含遮蔽後的金鑰識別片段，最新帳本已進一步去除該片段，保留清理前 JSON hash；完整金鑰未輸出。

歷史基準已依使用者提供的原作者65事件版本校正為151筆：保留未改寫的Fork150事件來源檔，補回3/31缺漏1筆，另外5筆欄位校正及1筆明確校時均有差異紀錄。圖表採校正後基準；不是宣稱Fork150筆在輸出中逐字不變。詳見 docs/PINE_AUTHOR_HISTORY_FIX.md 與 data/author_history_reconciliation_audit.json。

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
    "completed_signal": 145,
    "completed_no_signal": 191,
    "pending_confirmation": 71,
    "technical_failure": 8,
    "input_failure": 4,
    "not_started": 247,
    "unknown": 0
  },
  "remaining_not_started_groups": 247,
  "remaining_not_started_platform_posts": 247,
  "latest_attempted_or_reviewed_date": "2026-11-06T22:07:49+08:00",
  "all_posts_visited_before_first_unstarted": "2026-09-23T10:02:01+08:00",
  "successfully_completed_contiguous_prefix": "2026-07-20T18:41:00+08:00",
  "first_unstarted_date": "2026-09-23T10:02:29+08:00",
  "latest_signal_date": "2026-09-22T18:54:02+08:00",
  "pine": {
    "historical_events": 151,
    "added_events": 143,
    "total_events": 294,
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
    "initialization_functions": 15,
    "max_events_per_function": 20,
    "first_bar_calls": 15,
    "event_initialization_chunk_limit": 20
  },
  "last_new_valid_response_date": "2026-09-23T08:59:55+08:00",
  "new_stop_post_date": "2026-09-23T10:02:01+08:00",
  "new_generation_attempts": 385,
  "new_http_responses": 385,
  "new_status_counts": {
    "pending_confirmation": 58,
    "completed_no_signal": 183,
    "completed_signal": 138,
    "technical_failure": 6,
    "input_failure": 4
  },
  "service_reported_usage": {
    "input_tokens": 1094612,
    "output_tokens": 58849,
    "total_tokens": 1153461,
    "reasoning_tokens": 0
  },
  "new_validated_responses": 375,
  "images_attached": 263,
  "videos_unanalysed": 51,
  "http_responses_without_usage": 4,
  "service_reported_cached_input_tokens": 772992,
  "apify_http_counts": {
    "GET": 26,
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
  "stop_reason": "media_preflight_failure",
  "service_quota_statement": null,
  "all_history_fully_classified": false,
  "rule_sha256": "8ccd8bbe6388705261e7240897417683f2dc6e2016f5db9d5eca462533837162",
  "provider_model_and_reasoning": "Service-reported gpt-5-mini / minimal, not independently verified",
  "usage_tracking_note": "ChatAnywhere request accounting is from durable ledgers; legacy usage.json ai_attempts is not the cumulative ChatAnywhere total.",
  "accounting_note": "Post counts include all prior tests, failures, reviews and cross-platform members; Pine counts are events, not posts. Tokens are service reports, not points or verified bills.",
  "current_session": {
    "id": "20261111-01",
    "generation_attempts": 1,
    "validated_responses": 1,
    "added_events": 0,
    "pine_count_delta_since_session": 0,
    "historical_reference_event_delta_since_session": 0,
    "service_reported_usage": {
      "input_tokens": 2367,
      "output_tokens": 109,
      "total_tokens": 2476,
      "reasoning_tokens": 0
    },
    "status_counts": {
      "completed_no_signal": 0,
      "completed_signal": 0,
      "input_failure": 3,
      "pending_confirmation": 1,
      "technical_failure": 0
    },
    "actor_runs_started": 0,
    "saved_dataset_get_requests": 2,
    "actual_points_deducted": null,
    "run_url": "https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42993255197",
    "stop_http_status": null,
    "media_diagnostic": "data/history_media_diagnostic_20261111.json"
  },
  "media_blocker": {
    "new_input_failures": 3,
    "generation_attempts_for_failed_posts": 0,
    "confirmed_image_http_403": 2,
    "confirmed_image_timeouts": 1,
    "diagnostic": "data/history_media_diagnostic_20261111.json",
    "cause": "Signed image URL timestamps precede probes, but expiration semantics and sole cause unverified. No TLS bypass or generation retry."
  }
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

下一筆尚未處理日期為 2026-09-23T10:02:29+08:00（Asia/Taipei）。資料 cutoff 維持不變，恢復媒體只讀既有 dataset，不另啟動 Actor。每次續跑將先前阻塞與基準用量保留在 control，只有本次明確授權的入口才能繼續；完成、待確認、失敗與 unknown 不自動重送。

本次 API 次數僅指 AI 生成及 Apify 啟動／讀取；GitHub 進度保存與圖片下載另計，沒有把上述數字宣稱為全部 HTTP 流量。data/usage.json 的 ai_attempts 為舊流程計數，不等於 ChatAnywhere 全部呼叫量，應以本次及既有帳本查核。

只做一次性執行，不啟用持續排程、不發布 Pages、不合併 PR。

## 2026/11/11 續跑與圖片存取阻塞

本輪只有1次AI生成（HTTP 200）：2026/9/23 08:59:55貼文資訊不足，保留待確認；不是新訊號。接下來三篇在送出AI前發生圖片問題，attempts均為0：Facebook 9/23 09:02:50逾時，Threads 9/23 09:39:13與10:02:01遭HTTP拒絕。連續三筆觸發既有共同故障保護，未自動重送、未當成完成。

另以相同公網IP固定、TLS、主機白名單、大小及逾時防護做三次有上限的圖片GET診斷；Threads兩張確為HTTP 403，Facebook再次逾時。三個URL的oe時間戳提示均早於測試時刻，但oe語意與過期是否唯一原因未獨立驗證。沒有保存完整URL、query、錯誤body或憑證；原始模型回應與圖片失敗分開保存。診斷不呼叫AI、不啟動Actor、不發通知。

完整候選仍為294事件＝151原歷史＋143累計新增，本輪新增0事件。來源總666篇：145有訊號、191無訊號、71待確認、8技術失敗、4輸入失敗、0狀態不明、247尚未開始。下一篇未開始為9/23 10:02:29；既有3篇本輪媒體失敗仍列失敗，不自動轉回未處理。

服務回報本輪input2367／output109／total2476 tokens。實際扣點、剩餘免費請求與重設時刻未回傳，不能當作零扣點或99次餘額。本次已確認的停止原因是媒體存取，不是免費額度耗盡。固定使用ChatAnywhere .tech/v1、gpt-5-mini／minimal；模型與推理僅服務回報，非獨立驗證。Apify新增Actor0，既有Dataset唯讀2次，共用Actor計數仍48／70。

沿用網站／原生策略9/30公開截止，完整歷史候選繼續保留原scope；策略輸出改由完整候選擷取截止前原樣事件，並重新分段初始化。測試改為以保存資料與截止時間核對，移除294／45這類會隨續跑過時的數字，沒有新增情緒條件或AI驗收樣本。策略成交引擎、日盤尾棒修正、預設日期及風控未改動。重建使用保存判讀與行情，未重新判讀或擷取行情。

本輪與圖片診斷一次性入口均已停用，控制帳本已封存。需要可讀的媒體來源後才能安全解除共同故障；不以關閉TLS／網域限制、忽略圖片或直接重送失敗資料繞過。未啟用排程、未部署網站、未發Telegram、未合併PR。Pine靜態檢查／離線測試不等於TradingView實際編譯或策略執行。
