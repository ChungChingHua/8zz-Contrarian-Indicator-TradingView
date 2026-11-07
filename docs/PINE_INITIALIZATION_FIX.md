# CE10205：事件初始化區塊過長

使用者提供的完整腳本含 187 筆事件，與 PR 最新候選僅差結尾空行。`if barstate.isfirst` 一次包含 935 個 `array.push`，TradingView 畫面回報 `The if statement is too long (CE10205)`。

已改為 10 個全域初始化函式，每個最多 20 筆事件（100 個 push），首根 K 棒的 `if` 僅依序呼叫這 10 個函式。函式只修改已宣告陣列的內容，不重新指派全域陣列參考；每個函式以固定 `0` 回傳。事件仍只在第一根 K 棒初始化一次。

共用格式器為 `scripts/pine_initialization.py`；原作者政策候選產生器及原有 social 產生器均已接入。保留 `data/historical-indicator.pine` 作為不變的原始歷史來源，不直接改寫該檔案。最新版完整輸出為 `candidates/8zz-history-latest.pine`，仍為 187 事件；根目錄原有 150 事件輸出亦採相同初始化結構。

離線檢查：

- 使用者提供的 187 筆事件，其時間、方向、強度、提示文字、標的及順序與修正版逐欄相同。
- 初始化區塊以外的腳本內容逐字不變，包含顯示、箭頭、背景、濾網、績效及提醒。
- 133 項離線測試通過；新增回歸測試涵蓋分段邊界、跳脫字元、800 筆結構成長、重跑一致性，以及拒絕遺失非事件邏輯。
- 原作者規則雜湊不變，沒有新增 AI 或 Apify 請求；資料處理與免費額度停止狀態不變。
- 尚未在 TradingView 實際編譯此修正版。20 筆是本專案採用的分段大小，不是官方公布的固定編譯上限，亦不保證未來不會遇到其他編譯限制。

官方依據：

- [TradingView 官方錯誤文件：The if statement is too long](https://www.tradingview.com/pine-script-docs/v5/error-messages/#the-if-statement-is-too-long)：建議拆成較小函式或條件區塊；該錯誤說明在 v5 文件中仍可查閱。
- [Pine v6 User-defined functions](https://www.tradingview.com/pine-script-docs/language/user-defined-functions/#function-scopes)：函式不能重新指派全域變數，但可以用 setter 修改全域 reference type 的物件內容。

在 TradingView Pine Editor 全選取代為最新版完整候選，儲存並加入／更新圖表。GitHub 不會自動同步 TradingView。本修正沒有重跑歷史判讀、啟用排程、發布 Pages 或合併 PR。
