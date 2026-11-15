# TradingView CE10117：兩份Pine的token修正

使用者截圖顯示指標114748、策略116055個compiled tokens，均超過100256。前次235項Python測試未經TradingView編譯，沒有驗證此限制，不能以測試通過推定可載入。

## 修正

指標與策略都改為packed-v1初始化：5個共用array.push陳述載入資料，不再為362事件重複編譯1810個寫入陳述。每段最多20事件、30000 UTF-8 bytes，本版19段、最大10249 bytes；低於官方40960字元字串上限。分段也保留先前避免if過長的措施。

完整tooltip、時間、方向、強度及ticker未截短或刪除。五欄原資料仍以單行註解保留供既有離線讀取工具使用，註解不屬於Pine執行碼；真正載入的packed payload另有逐筆解碼比對，不能只靠註解宣稱事件完整。百分號、欄／列分隔符、引號、反斜線、換行及Unicode均有無損測試。時間轉數字測試保留毫秒精度。

兩份各362事件，和修正前逐筆相同；初始化之前與之後的指標／策略運算程式也已比對不變。A/B出場、ATR／獲利移動停損、4/9校正、原作者情緒規則及歷史署名均保留。根目錄舊相容指標也一併使用相同新載入器，但最新362事件交付仍以下方兩份為準。

## 交付

- [完整指標](../candidates/8zz-history-latest.pine)
- [完整策略](../candidates/8zz-strategy-latest.pine)
- [同版SHA256及事件資料hash](../candidates/8zz-pine-delivery.json)
- [指標檢查](../candidates/8zz-history-latest.checks.json)／[策略檢查](../candidates/8zz-strategy-latest.checks.json)

請分別完整取代兩份腳本，不把碼接在舊版本後方；儲存後加入／更新圖表。策略仍為標準30分鐘日盤，操作參閱[PINE_STRATEGY](PINE_STRATEGY.md)。GitHub不會自動更新TradingView。

## 驗證與限制

240項離線回歸通過。新增packed實際資料與canonical五欄往返檢查、分隔符／百分號／Unicode、payload或解碼器被改動時拒絕、舊初始化升級、大Unicode字串分段，以及1／362／800事件時可執行事件寫入數保持5個的檢查。兩份原始碼約312KB／311KB，小於官方5MB編譯請求限制；這些數字不是compiled tokens。

**尚未在TradingView實際重新編譯，沒有可回報的新版compiled token數，也不能宣稱已驗證低於100256。** 官方說明無法直接檢查成功編譯腳本的IL大小，超限時才會顯示數字。本次透過降低重複的執行碼處理已確認的問題，不用原始碼長度或Python測試冒充平台驗證。

未呼叫AI、Apify、Telegram；未重新抓取、未改任何判讀／進度／通知狀態，沒有啟用排程、網站發布或合併PR。網站九月底範圍不變。後續同一生成流程仍產出指標與策略兩份完整Pine。

官方依據：
- [Compiled tokens與編譯請求限制](https://www.tradingview.com/pine-script-docs/writing/limitations/#compiled-tokens)：100256 compiled tokens、IL大小無直接查詢、建議減少重複碼及嵌入資料；5MB請求限制包含註解等原始碼。
- [Strings](https://www.tradingview.com/pine-script-docs/concepts/strings/)：字串最多40960 encoded characters，str.split／str.replace_all等字串操作。
