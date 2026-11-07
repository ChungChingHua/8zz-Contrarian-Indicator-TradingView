## 本輪實際檢查與保留疑點

- [首段執行](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42354590261)：媒體前檢失敗，0生成，已遠端保存。
- [無金鑰診斷](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42365658302)：CDN僅IPv6、errno101；沒有生成。
- [恢復未送出資料](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42366144151)：第一筆HTTP200生成1次，誠實未讀圖片註記被舊本地數量檢查拒絕，原JSON完整保存。
- [離線重驗後續未開始4篇](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42366512318)：首筆不重送，續4次，最終遠端帳本finished=true、總5次、每篇1次。原始回應hash與修正歷史可稽核。

125項離線測試與Python編譯檢查通過；恢復、stale CAS、quota、格式錯誤、送出後中斷、結果提交失敗、unknown禁止重送均已模擬。Pine只做結構檢查，未實際TradingView編譯。

第2筆圖像轉錄含6505／台塑化。服務回傳6505.TWO，但[證交所公開公司資料](https://openapi.twse.com.tw/v1/opendata/t187ap03_L)列台塑化於2003-12-26上市（TWSE），因此僅校正yfinance市場後綴為6505.TW；原服務ticker仍留raw及original_ai_ticker，靜態參照與hash另存data/static_ticker_reference.json。查核沒有取得後續價格，也沒有回灌情緒；方向+1與強度3未改。PR最新候選檔包含此靜態資料修正，早先Actions artifact是執行當時版本，使用前應取PR最新檔。

服務對第2筆理由提到「委託／成交介面」，但其實際轉錄沒有原作者強制booster片語；本地order_proof_rule_matched=false，**保留的是AI原評強度3，不宣稱已證明真實成交**。原規則允許非委託的極端情緒評3，不能反過來增設「沒成交文字不得評3」的新門檻。圖像與情緒解讀仍是服務回報，候選供檢查，不是準確性或交易績效保證。

本輪模型清單／帳號餘額查詢0；另做不帶金鑰的公開DNS、來源照片頁與證交所靜態資料查核，不屬生成，也不把這些控制／參照請求混進5次模型請求。沒有重新付費抓Apify歷史。

## 手動入口與停止狀態

Actions → **Original-author history batch (manual)** → Run workflow → 選PR分支`codex/social-pipeline-20261106`。現在固定batch已finished、5次授權耗盡，預設再啟動只讀帳本，不會再生成。恢復選項預設false；只有程式中嚴格限定的零生成或已保存HTTP200本地校正狀態能使用，不能重試API／額度錯誤或unknown。新批次需另行授權並固定新計畫，不能改ID繞過。

已移除臨時push觸發，不啟用schedule或Pages，不合併PR。舊smoke／品質入口仍停用，一般pause=true。正式archive與正式8zz-indicator.pine不變，交付完整候選152事件（歷史150＋本批2）；待確認那篇沒有新箭頭。

