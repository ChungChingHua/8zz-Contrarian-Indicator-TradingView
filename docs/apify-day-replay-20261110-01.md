# 2026/11/10 交易日抓取成本：事後重播

**這是事後重播成本，不能當成當日即時偵測延遲或資料完整性驗證。**

執行狀態：`completed`；遠端帳本 `apify-day-replay-20261110-01`。已保存 Dataset 結果的成功 run：40／40；啟動預留：40／40。

實際執行時間（台灣）：2026-11-10T14:46:06.892986+08:00 ～ 2026-11-10T14:58:28.760237+08:00。

模擬 2026/11/10 台灣時間 08:45～13:30，每 15 分鐘一輪、20 輪。首輪獨立基礎游標為 11/9 13:30，實際查詢由 11/9 11:30 開始。後續依各平台上次成功測試游標往前兩小時，到該輪截止時間；受限時不推進。所有時間區間採起點包含、終點不包含。

## 成本與用量

| 平台 | run 數 | 有效文章回傳數（含重複） | 診斷列 | 重複數 | 首次新增數 | 最新 usageTotalUsd 合計 |
|---|---:|---:|---:|---:|---:|---:|
| facebook | 20 | 17 | 9 | 13 | 4 | US$0.202 |
| threads | 20 | 28 | 0 | 22 | 6 | US$0.455 |

**全天 API 最新可觀測值：US$0.657。**

只加總每次 `usageTotalUsd` 一次。`usageUsd` 是分項，計費事件是明細，`externalChargedTotalUsd` 是另一欄位，全部獨立保存、不重複相加。官方文件指出 usageTotalUsd 為 run 總成本，而 externalChargedTotalUsd 僅適用 multi-tenant Standby 對其他使用者的計費；未把它視為本次額外帳單。

每個已知 run 完成後都安排一次唯讀刷新；沒有為費用查詢啟動新 run。原始提交／初次完成／最後查詢快照都保存在獨立帳本。若仍有成本缺失或刷新失敗，見下列清單。即使事件計數已對帳，也未獨立核對最終已結算帳單，API 數值仍可能延遲更新，零不代表免費。

官方依據：[啟動費用上限](https://docs.apify.com/api/v2/actors-runs-post)、[run 費用定義與完成後可能延遲](https://docs.apify.com/api/v2/actor-run-get)。

每月共用啟動帳：8 → 48／70；本次授權上限 US$4.00（40×US$0.10），不是實際扣款。預留在提交前經 GitHub CAS 保存；結果不明不得重送。

Apify HTTP 請求：`{"GET": 188, "POST": 40}`。POST 包括啟動與任何必要的安全中止，實際啟動以各 run 與預留明細為準；本次不進行 AI、Telegram、網站呼叫或媒體辨識。

費用延遲實測：29 次 run 的最後刷新金額不同於初次完成值。計費事件合計為 {"facebook": {"post": 26, "actor-start": 20, "filter-applied": 26}, "threads": {"start": 14, "profile": 0, "post": 35}}。計費事件數不等於有效文章數：Facebook 診斷列也有被計入 post／filter-applied，Threads post 計費事件亦多於有效文章回傳數；不能以文章數替代服務回報費用。

## 每月估算（不是報價或最終帳單）

| 交易日數 | 以本次全天 API 成本直接相乘 | 預計 Actor 啟動次數 |
|---|---:|---:|
| 20 | US$13.140 | 800 |
| 22 | US$14.454 | 880 |
| 23 | US$15.111 | 920 |

以上僅包含本次核實的抓取 run 成本，不包含 AI、Telegram、網站、匯率／稅、GitHub Actions 或其他未核實成本；文章量、定價、免費方案與延遲結算均可能改變。每天 40 次啟動對應每月 800／880／920 次，**超過現有每月 70 次保護值**；此估算不代表現有流程可以連續跑完整月。本次沒有提高保護值或啟用排程。

## Actor 與參數

- facebook：`apify~facebook-posts-scraper`；實際版本：0.0.413 (`ndtSgN95ZPtNihh5c`)
- threads：`automation-lab~threads-scraper`；實際版本：0.1.68 (`u7xlWkUJn0xIkKQVC`)

沿用正式流程的 input：Facebook startUrls／resultsLimit=50／onlyPostsNewerThan／onlyPostsOlderThan；Threads mode=posts／usernames=[banini31]／maxPosts=50／includeProfile=false／postedAfter／postedBefore。離線測試直接擷取正式 input 分支比對。query 參數 timeout=180、memory=512、maxItems=50、maxTotalChargeUsd=0.10；restartOnError=false，禁止平台重啟。實際 options、版本與 build ID 都保存於逐 run 帳本；若平台調整實際記憶體，以 options 為準。

## 逐輪、逐平台明細

全部為台灣時間（UTC+8）。「有效」限指定作者／Threads 明確非回覆非轉貼，且在該實際查詢區間內；「重複／新增」依**本次獨立帳本的平台＋貼文 ID**，不與正式文章帳本比對。相同內容若在兩平台各有 ID，仍分平台計數，不代表跨平台獨立文章總數。其他作者／回覆等排除數與窗外文章另見 JSON／CSV。

| 輪 | 截止 | 平台 | 實際查詢起點→終點 | 版本 | run ID | 狀態 | runTimeSecs | 有效 | 診斷 | 重複 | 新增 | US$ | 游標／受限 |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 08:45 | facebook | 2026-11-09 11:30 → 2026-11-10 08:45 | 0.0.413 | `MXhmyJIHGVMwSRnIM` | SUCCEEDED | 9.185 | 3 | 0 | 0 | 3 | 0.022 | 推進 |
| 1 | 08:45 | threads | 2026-11-09 11:30 → 2026-11-10 08:45 | 0.1.68 | `TVMgaCk5hf6rxRD3Z` | SUCCEEDED | 5.677 | 3 | 0 | 0 | 3 | 0.035 | 推進 |
| 2 | 09:00 | facebook | 2026-11-10 06:45 → 2026-11-10 09:00 | 0.0.413 | `QF6JdWnedlwwg4uPD` | SUCCEEDED | 5.375 | 1 | 0 | 1 | 0 | 0.008 | 推進 |
| 2 | 09:00 | threads | 2026-11-10 06:45 → 2026-11-10 09:00 | 0.1.68 | `iJlqii0dTKD8w4TIH` | SUCCEEDED | 6.551 | 0 | 0 | 0 | 0 | 0 | 推進 |
| 3 | 09:15 | facebook | 2026-11-10 07:00 → 2026-11-10 09:15 | 0.0.413 | `ormQFzbtWeerOtiIJ` | SUCCEEDED | 4.967 | 1 | 0 | 1 | 0 | 0.008 | 推進 |
| 3 | 09:15 | threads | 2026-11-10 07:00 → 2026-11-10 09:15 | 0.1.68 | `mswhTBTOhsYd8IJrg` | SUCCEEDED | 6.376 | 0 | 0 | 0 | 0 | 0 | 推進 |
| 4 | 09:30 | facebook | 2026-11-10 07:15 → 2026-11-10 09:30 | 0.0.413 | `ywZRkpSaAebFFevZ0` | SUCCEEDED | 15.601 | 2 | 0 | 1 | 1 | 0.015 | 推進 |
| 4 | 09:30 | threads | 2026-11-10 07:15 → 2026-11-10 09:30 | 0.1.68 | `CwQcq7PXI6qq7qINQ` | SUCCEEDED | 5.35 | 0 | 0 | 0 | 0 | 0 | 推進 |
| 5 | 09:45 | facebook | 2026-11-10 07:30 → 2026-11-10 09:45 | 0.0.413 | `iFDNLcKhGtusw9yNA` | SUCCEEDED | 3.682 | 0 | 1 | 0 | 0 | 0.008 | 推進；離線比對未回傳 2 篇 |
| 5 | 09:45 | threads | 2026-11-10 07:30 → 2026-11-10 09:45 | 0.1.68 | `DUOqGvzI1lb9BpeRl` | SUCCEEDED | 4.979 | 0 | 0 | 0 | 0 | 0 | 推進 |
| 6 | 10:00 | facebook | 2026-11-10 07:45 → 2026-11-10 10:00 | 0.0.413 | `5ILbdTjXzMTzLwpkg` | SUCCEEDED | 31.959 | 2 | 0 | 2 | 0 | 0.015 | 推進 |
| 6 | 10:00 | threads | 2026-11-10 07:45 → 2026-11-10 10:00 | 0.1.68 | `PjmdrRN6cUY3uRFfI` | SUCCEEDED | 3.998 | 0 | 0 | 0 | 0 | 0 | 推進 |
| 7 | 10:15 | facebook | 2026-11-10 08:00 → 2026-11-10 10:15 | 0.0.413 | `hk3TteEjm3dbxBmCt` | SUCCEEDED | 6.098 | 2 | 0 | 2 | 0 | 0.015 | 推進 |
| 7 | 10:15 | threads | 2026-11-10 08:00 → 2026-11-10 10:15 | 0.1.68 | `8PbOhmSlYYa2xm7vJ` | SUCCEEDED | 4.992 | 0 | 0 | 0 | 0 | 0 | 推進 |
| 8 | 10:30 | facebook | 2026-11-10 08:15 → 2026-11-10 10:30 | 0.0.413 | `3QsJ1gtb6xToruZPS` | SUCCEEDED | 17.584 | 2 | 0 | 2 | 0 | 0.015 | 推進 |
| 8 | 10:30 | threads | 2026-11-10 08:15 → 2026-11-10 10:30 | 0.1.68 | `pOhCLNgleFNllhKIs` | SUCCEEDED | 5.054 | 1 | 0 | 0 | 1 | 0.025 | 推進 |
| 9 | 10:45 | facebook | 2026-11-10 08:30 → 2026-11-10 10:45 | 0.0.413 | `FmJMqtGYXG5Ei3djK` | SUCCEEDED | 4.89 | 1 | 0 | 1 | 0 | 0.008 | 推進 |
| 9 | 10:45 | threads | 2026-11-10 08:30 → 2026-11-10 10:45 | 0.1.68 | `WlibTWniKSYUOEyrC` | SUCCEEDED | 6.654 | 1 | 0 | 1 | 0 | 0.025 | 推進 |
| 10 | 11:00 | facebook | 2026-11-10 08:45 → 2026-11-10 11:00 | 0.0.413 | `mQuisgE588RM8u2r8` | SUCCEEDED | 7.18 | 1 | 0 | 1 | 0 | 0.008 | 推進 |
| 10 | 11:00 | threads | 2026-11-10 08:45 → 2026-11-10 11:00 | 0.1.68 | `7uTdyKiApCagAMvPD` | SUCCEEDED | 6.38 | 2 | 0 | 1 | 1 | 0.03 | 推進 |
| 11 | 11:15 | facebook | 2026-11-10 09:00 → 2026-11-10 11:15 | 0.0.413 | `ydaXEEODEYkxZ2lvb` | SUCCEEDED | 15.375 | 1 | 0 | 1 | 0 | 0.008 | 推進 |
| 11 | 11:15 | threads | 2026-11-10 09:00 → 2026-11-10 11:15 | 0.1.68 | `p9xlcRwompwulTf98` | SUCCEEDED | 4.102 | 2 | 0 | 2 | 0 | 0.03 | 推進 |
| 12 | 11:30 | facebook | 2026-11-10 09:15 → 2026-11-10 11:30 | 0.0.413 | `TDodssCJIiWLFrOIv` | SUCCEEDED | 3.445 | 1 | 0 | 1 | 0 | 0.008 | 推進 |
| 12 | 11:30 | threads | 2026-11-10 09:15 → 2026-11-10 11:30 | 0.1.68 | `TLmrNwdpdtT5t4rGy` | SUCCEEDED | 3.554 | 2 | 0 | 2 | 0 | 0.03 | 推進 |
| 13 | 11:45 | facebook | 2026-11-10 09:30 → 2026-11-10 11:45 | 0.0.413 | `b4TQdvZARxDfSNLwc` | SUCCEEDED | 4.614 | 0 | 1 | 0 | 0 | 0.008 | 推進 |
| 13 | 11:45 | threads | 2026-11-10 09:30 → 2026-11-10 11:45 | 0.1.68 | `JhBwQD109rIaGvNSP` | SUCCEEDED | 4.771 | 2 | 0 | 2 | 0 | 0.03 | 推進 |
| 14 | 12:00 | facebook | 2026-11-10 09:45 → 2026-11-10 12:00 | 0.0.413 | `ri6zWY7Qz8zCzhN3u` | SUCCEEDED | 3.532 | 0 | 1 | 0 | 0 | 0.008 | 推進 |
| 14 | 12:00 | threads | 2026-11-10 09:45 → 2026-11-10 12:00 | 0.1.68 | `wrntgz0A8meWqn5a3` | SUCCEEDED | 7.921 | 3 | 0 | 2 | 1 | 0.04 | 推進 |
| 15 | 12:15 | facebook | 2026-11-10 10:00 → 2026-11-10 12:15 | 0.0.413 | `ftcalJJrLlsWml6JQ` | SUCCEEDED | 7.139 | 0 | 1 | 0 | 0 | 0.008 | 推進 |
| 15 | 12:15 | threads | 2026-11-10 10:00 → 2026-11-10 12:15 | 0.1.68 | `q9dBLxmyUE8K6CTJg` | SUCCEEDED | 4.323 | 3 | 0 | 3 | 0 | 0.04 | 推進 |
| 16 | 12:30 | facebook | 2026-11-10 10:15 → 2026-11-10 12:30 | 0.0.413 | `bqSoY71uueYqAudp8` | SUCCEEDED | 27.284 | 0 | 1 | 0 | 0 | 0.008 | 推進 |
| 16 | 12:30 | threads | 2026-11-10 10:15 → 2026-11-10 12:30 | 0.1.68 | `qM9OH7YzoEZLCiKDx` | SUCCEEDED | 6.05 | 3 | 0 | 3 | 0 | 0.04 | 推進 |
| 17 | 12:45 | facebook | 2026-11-10 10:30 → 2026-11-10 12:45 | 0.0.413 | `TytSeDcdjmUYAVPgh` | SUCCEEDED | 4.028 | 0 | 1 | 0 | 0 | 0.008 | 推進 |
| 17 | 12:45 | threads | 2026-11-10 10:30 → 2026-11-10 12:45 | 0.1.68 | `0QfL1dW12FgZnZIAT` | SUCCEEDED | 3.949 | 2 | 0 | 2 | 0 | 0.035 | 推進 |
| 18 | 13:00 | facebook | 2026-11-10 10:45 → 2026-11-10 13:00 | 0.0.413 | `0D02MfXJcA9cfOQyH` | SUCCEEDED | 5.334 | 0 | 1 | 0 | 0 | 0.008 | 推進 |
| 18 | 13:00 | threads | 2026-11-10 10:45 → 2026-11-10 13:00 | 0.1.68 | `WtSFzLrRdWNhy5gau` | SUCCEEDED | 4.998 | 2 | 0 | 2 | 0 | 0.035 | 推進 |
| 19 | 13:15 | facebook | 2026-11-10 11:00 → 2026-11-10 13:15 | 0.0.413 | `Oj9NE5ScBXIT9vPC6` | SUCCEEDED | 4.273 | 0 | 1 | 0 | 0 | 0.008 | 推進 |
| 19 | 13:15 | threads | 2026-11-10 11:00 → 2026-11-10 13:15 | 0.1.68 | `kWt9Urhq4kCqkuhm8` | SUCCEEDED | 10.981 | 1 | 0 | 1 | 0 | 0.03 | 推進 |
| 20 | 13:30 | facebook | 2026-11-10 11:15 → 2026-11-10 13:30 | 0.0.413 | `OOXjrQahLFqRxZtAL` | SUCCEEDED | 4.687 | 0 | 1 | 0 | 0 | 0.008 | 推進 |
| 20 | 13:30 | threads | 2026-11-10 11:15 → 2026-11-10 13:30 | 0.1.68 | `ttRbjiJIOVqzJI5Xw` | SUCCEEDED | 4.155 | 1 | 0 | 1 | 0 | 0.03 | 推進 |

## 未完成、受限與可能漏資料

不可因 Actor SUCCEEDED 就認定資料完整。50 筆結果、費用達上限／截斷訊息、不明 schema、技術失敗等均標記，測試游標不因此推進。`no_items` 診斷列單獨列數，不當文章；已知 no_items 本身不直接認定失敗。

- 不完整 run 時間窗：0
- 尚未嘗試的輪／平台：0
- 離線比對有回傳差異的時間窗：1
- 缺失成本：[]
- 尚未完成最終唯讀費用刷新 run 數：0
- 停止原因：無
- 費用刷新異常：null
- 最終測試游標：{"facebook": "2026-11-10T13:30:00+08:00", "threads": "2026-11-10T13:30:00+08:00"}

離線比對發現下列時間窗未回傳本次其他輪曾取得、且發文時間落在查詢範圍內的文章。這是可能漏資料或回傳不穩定的證據；不能單憑此判定原因或當日是否可取得，也不把 no_items 直接判為抓取失敗。保留當時模擬游標行為，不重跑、不修改正式流程。

```json
[
  {
    "round": 5,
    "source": "facebook",
    "run_id": "iFDNLcKhGtusw9yNA",
    "query_start_taipei": "2026-11-10T07:30:00+08:00",
    "query_end_taipei": "2026-11-10T09:45:00+08:00",
    "missing_previously_or_elsewhere_observed_keys": [
      "facebook:1708163567334898",
      "facebook:1708197577331497"
    ]
  }
]
```

## 隔離與證據

只讀 Git tree SHA 核對正式資料，沒有讀取正式成功截止時間作為測試游標。正式資料／Pine／通知與正式 workflow 共 91 檔的前後 blob SHA 比較結果：**True**。測試文章、游標、去重、run 與費用使用獨立帳本；共用帳本只更新啟動預留與費用。

- [逐輪 CSV](apify-day-replay-20261110-01.csv)
- [獨立遠端進度與費用帳本](../data/cost_tests/apify-day-replay-20261110-01.json)
- [獨立測試文章與去重帳本](../data/cost_tests/apify-day-replay-20261110-01-posts.json)

離線驗證：10 項 replay 測試涵蓋 40 次上限、月保護、隔離、費用不重複加總、區間／重疊、無重試、額度停止、受限不推進、延遲費用使游標失效，以及正式 input 相同。未變更情緒規則，沒有重新判讀情緒。完成後停用本次線上測試入口；不啟用正式排程、不發布網站、不合併 PR。
