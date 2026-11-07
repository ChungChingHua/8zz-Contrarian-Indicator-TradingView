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

若Actions介面顯示 **Original-author history batch (manual)** 的Run workflow，可選PR分支`codex/social-pipeline-20261106`；若未顯示，使用下方已實測的專用workflow ID／CLI，不使用舊抓取入口。現在固定batch已finished、5次授權耗盡，預設再啟動只讀帳本，不會再生成。恢復選項預設false；只有程式中嚴格限定的零生成或已保存HTTP200本地校正狀態能使用，不能重試API／額度錯誤或unknown。新批次需另行授權並固定新計畫，不能改ID繞過。

已移除臨時push觸發，不啟用schedule或Pages，不合併PR。舊smoke／品質入口仍停用，一般pause=true。正式archive與正式8zz-indicator.pine不變，交付完整候選152事件（歷史150＋本批2）；待確認那篇沒有新箭頭。


## 真正手動dispatch已驗證（沒有新增生成）

專用workflow ID **410173704** 已註冊，並直接以workflow_dispatch指定PR分支驗證成功。沒有借用舊fetch／Apify／Pages入口，也沒有修改main或合併PR。

- [只帶GitHub token的驗證器](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42368389109)：先GET檢查固定batch已finished／5次耗盡，再GET確認專用workflow ID的path與active狀態，才POST固定PR ref；HTTP204。
- [真正workflow_dispatch執行](https://github.com/ChungChingHua/8zz-Contrarian-Indicator-TradingView/actions/runs/42368398192)：事件workflow_dispatch，branch=codex/social-pipeline-20261106，worker直接讀已完成帳本，預留／生成仍5次，所有原回應hash不變，沒有新provider request。
- `data/history_manual_dispatch_verification.json`保存驗證摘要；一次性push驗證器現已停用，actions:write與GH_TOKEN注入已移除。只留下contents:read的if:false stub。

PR未合併時，GitHub網頁可能不顯示新workflow的Run workflow按鈕。可用已登入GitHub的CLI明確指定專用ID與PR分支：

```bash
gh workflow run 410173704 --repo ChungChingHua/8zz-Contrarian-Indicator-TradingView --ref codex/social-pipeline-20261106
```

這是雲端手動入口，不要求在聊天貼金鑰。**目前batch已完成且5次用完，所以此命令只復核帳本／重建同一候選，不會生成新資料。** 新一批必須另行授權、凍結新計畫，不能靠更換run ID重送。不要選main或舊的Fetch FB Events工具；舊入口沒有在本輪啟用。

先前曾考慮橋接舊的預設分支workflow，自動審查因可能誤跑舊Apify流程而拒絕，該推送未執行。已改用上述專用ID、已耗盡帳本前檢的安全替代路徑並實測通過；沒有繞過被拒的舊路徑。最終127項離線測試與CI通過，Pine仍未經TradingView編譯。
