> **線上功能暫停，請勿設定後直接執行 smoke。** 本次資安審查不授權模型查詢、貼文／圖片傳送、排程或合併。見[資安審查](docs/SECURITY_REVIEW.md)。

> 目前 PR 使用獨立 ChatAnywhere 免費版設定，僅允許兩筆 smoke、無排程及批次。見[目前供應商設定](docs/CHATANYWHERE.md)；先前 OpenAI 官方說明保留作歷史參考。

# 8zz 巴逆逆反指標 (8zz Banini Reverse Indicator)

> **免責聲明：本指標僅供娛樂參考，不構成任何投資建議。**  
> © hansai-art | [Mozilla Public License 2.0](https://mozilla.org/MPL/2.0/)

---

## 這是什麼？

**「別人恐慌時貪婪，別人貪婪時恐慌。」**

本指標追蹤[巴逆逆](https://www.facebook.com/DieWithoutBang)的發文情緒，並以**逆向思維**產生買賣訊號：

| 巴逆逆情緒 | 指標方向 | 背後邏輯 |
|-----------|---------|---------|
| 恐慌、被套、停損、痛苦 | 偏多 ▲ | 散戶最恐慌的時刻 = 底部附近 |
| 追漲、自大、歡呼 | 偏空 ▼ | 散戶最亢奮的時刻 = 頂部附近 |

> **核心原則：情緒 > 動作。** 就算他正在買進，但情緒是痛苦與被套，指標仍偏多▲。

---

## 📊 即時戰績看板

**👉 [ChungChingHua.github.io/8zz-Contrarian-Indicator-TradingView](https://ChungChingHua.github.io/8zz-Contrarian-Indicator-TradingView/)**

已新增 Facebook＋Threads 有限額的雲端更新與完整 Pine 生成；請先閱讀[自動化操作與驗證狀態](docs/AUTOMATION.md)。上傳資料已匯入，未完成 AI／圖片辨識者保留待處理；小量驗證成功前不啟用付費排程。GitHub 更新後仍須手動貼入 TradingView。

### 目前戰績

勝率、勝負與平均報酬會隨事件及行情更新，請以[即時戰績看板](https://ChungChingHua.github.io/8zz-Contrarian-Indicator-TradingView/)為準；README 不再硬編碼容易過期的數字。

> **Mode B**：下一個方向翻轉訊號出現時平倉  
> **Mode A**：進場後固定持有 17 根 30 分鐘K棒出場（≈ 8.5 小時 ≈ 2 個台股交易日）

#### 勝負計算規則

| 訊號方向 | 結果 | 計算方式 |
|---------|------|---------|
| 偏空 ▼（做空） | 價格下跌 ✓ | **勝** |
| 偏空 ▼（做空） | 價格上漲 ✗ | **敗**（做空虧錢） |
| 偏多 ▲（做多） | 價格上漲 ✓ | **勝** |
| 偏多 ▲（做多） | 價格下跌 ✗ | **敗**（做多虧錢） |

> 多空都計入虧損；勝率以已平倉非零交易為分母，持平、未平倉與行情不足另外列出。

---

## 實戰截圖

![即時戰績看板](assets/dashboard.jpg)

![TradingView 圖表](assets/tradingview.jpg)


## 如何加入或更新 TradingView

1. 開啟本儲存庫的 `8zz-indicator.pine`，按 Raw 複製**完整內容**；也可下載 Actions 的 `social-update` artifact。
2. 在 TradingView 開啟 Pine Editor，備份舊腳本後以完整檔案取代內容。
3. 儲存、加入圖表／更新圖表，確認編譯成功與事件標籤。
4. 使用提醒者需重建提醒，才會採用新腳本。

**GitHub 更新不會自動同步至 TradingView。** 原作者的[指標頁面](https://tw.tradingview.com/script/6pVuUMS1/)仍保留供參考，但本分支新資料須自行更新腳本。

建議使用 30 分鐘或 1 小時線。詳見[完整操作說明](docs/AUTOMATION.md)。

---

## 訊號怎麼看？

圖表上每個事件會顯示：

- **▲ 偏多**（綠色向上箭頭）：看漲偏多，可考慮買進或持有
- **▼ 偏空**（紅色向下箭頭）：看跌偏空，可考慮減碼或觀望
- **★☆☆ / ★★☆ / ★★★**：訊號強度，星星越多情緒越極端
- **Tooltip**：懸停或點擊可見原始 FB 發文摘要

方向翻轉（上一個訊號與這次不同）才是關鍵進場點，標記為翻轉訊號（Flip）並納入勝率統計。

![訊號示例](assets/001.jpg)

---

## 參數調整

![設定面板](assets/004.jpg)


| 分組 | 參數 | 預設 | 說明 |
|------|------|------|------|
| 顯示 | 箭頭距離 (ATR倍數) | 0.5 | 箭頭與K棒的距離 |
| 顯示 | 顯示背景色帶 | 開 | 有效訊號期間顯示偏多/偏空底色 |
| 訊號治理 | 固定觀察K棒數 | 17 | Mode A 固定出場K棒數（30 分鐘K棒，≈ 8.5 小時）|
| 訊號治理 | 訊號有效K棒 | 24 | 超過後視為過期 |
| 濾網 | EMA 趨勢濾網 | 關 | 開啟後只放行與趨勢同向的訊號 |
| 濾網 | RSI 動能濾網 | 關 | 只放行站上/跌破 50 的訊號 |
| 濾網 | ATR 波動濾網 | 關 | 低波動時不出手 |
| 濾網 | 高週期結構確認 | 關 | 用更高週期確認大方向 |
| 執行 | 標的類型 | 台股個股 | 影響訊號品質分數與停損建議 |
| 執行 | 基礎建議倉位 (%) | 20 | 品質分數換算後的建議倉位 |

---

## 授權

[Mozilla Public License 2.0](https://mozilla.org/MPL/2.0/) — 可自由使用、修改、衍生，但衍生作品須保留原授權。


目前進度：技術 smoke 已完成，正在進行**離線判讀品質驗證**。請先確認 [10篇候選原文、圖片與預期依據](docs/QUALITY_SAMPLES.md)；[語意一致性、標的證據與狀態分流](docs/SEMANTIC_QUALITY.md) 已加入。沒有新增生成請求，線上／排程／Pages仍停用，PR尚未合併。
