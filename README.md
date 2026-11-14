> **Apify 現行設定：** 已依使用者指示移除程式單次費用與每月啟動次數上限，保留去重、記帳與失敗停止。詳見[政策與驗證](docs/APIFY_LIMIT_POLICY.md)。此次不啟動抓取或 AI，排程保持關閉。

> **最新 Pine 交付：指標＋原生策略，共用全部 362 筆已保存事件。**
>
> [token上限修正版說明](docs/PINE_TOKEN_LIMIT_FIX.md) · [指標完整碼](candidates/8zz-history-latest.pine) · [策略完整碼](candidates/8zz-strategy-latest.pine) · [同版核對資訊](candidates/8zz-pine-delivery.json) · [策略操作](docs/PINE_STRATEGY.md)。未完成歷史判讀仍保留待處理，不因此產生訊號。之後每次歷史／正式流程更新會一併產生兩份 Pine；目前排程仍停用、PR未合併。
>
> 舊階段網站／Telegram驗收紀錄：[操作文件](docs/LIVE_PIPELINE_ACCEPTANCE.md)。這些舊看板或預覽的事件範圍不等於最新完整 Pine，未發布本次網站修改。

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

已接續 Facebook＋Threads 增量流程與完整 Pine 生成；目前操作以[驗收與續接方法](docs/LIVE_PIPELINE_ACCEPTANCE.md)為準。上傳資料已匯入，未完成 AI／圖片辨識者保留待處理；小量驗證成功前不啟用付費排程。GitHub 更新後仍須手動貼入 TradingView。

### 目前戰績

本次看板尚未發布，請以 PR 的離線預覽 ZIP 與保存 JSON 驗收；既有公開網址可能仍是舊版。看板分開顯示發文時間的歷史參考與實際判讀完成後的可成交參考。舊事件缺完成時間者獨立列缺資料，不捏造即時績效。

> **Mode B**：下一個方向翻轉訊號出現時平倉  
> **Mode A**：進場後固定持有 17 根 30 分鐘K棒出場（≈ 8.5 小時 ≈ 2 個台股交易日）

#### 勝負計算規則（可核對版本）

多、空報酬均以方向 ×（出場價 / 進場價 − 1）計算。正報酬為勝、負報酬為敗、零為平手；勝率分母為勝＋敗＋平手，未平倉只顯示浮動報酬。已修正先前多單虧損不計敗的口徑。

本 PR 的可核對看板在 `docs/index.html`，顯著標示**部分資料績效**。它使用 `candidates/8zz-history-latest.pine` 的 257 個已保存事件，未呼叫 AI 或 Apify。所有交易統一採 **0050.TW 代理**，不是各事件原標的實績。資金起始 100、單一 100% 名目部位、不重疊、不加碼，出場按淨值複利，期間浮動損益計入曲線；未納入手續費、稅、滑價、股息及借券限制。

網站 Mode A 嚴格為 17 根 30 分鐘，缺歷史半小時行情時明列缺資料，不使用日線／小時線替代；Mode B 使用日線，在訊號後第一個已完成收盤成交，反向時平倉再反向。歷史參考成交嚴格晚於發文；可成交參考嚴格晚於發文及實際判讀完成，已錯過收盤不回填。同方向事件不另進場。Pine 在圖表標的與圖表週期收盤成交；只有使用 0050 且相同週期時才具有比較基礎，網站 B 日線不能宣稱與 30 分鐘 Pine 相同。Pine A 已改獨立持倉至固定期限，期間翻轉不覆寫 A，B 仍按反向訊號平倉。

參數已核對：`holdBars=17`、`signalLifeBars=24`，濾網預設關閉；24 根僅控制顯示有效期、不自動平倉。詳見 [看板驗證與更新方法](docs/DASHBOARD_AUDIT.md)。原作者網站連結保留，尚未發布本次修改。

---

## 實戰截圖

![即時戰績看板](assets/dashboard.jpg)

![TradingView 圖表](assets/tradingview.jpg)


## 如何加入或更新 TradingView

指標、策略同棒多空訊號都以最後發文情緒為準；先選最後一筆，再套濾網及顯示／交易。全部原事件保留。[同棒處理說明](docs/PINE_SAME_BAR_POLICY.md)。

目前策略為大台固定1口：起始本金／每口開倉保證金NT$700,000，每點NT$200，每口買賣各計稅金＋手續費NT$250（來回NT$500）。固定保證金採程式資金檢查，詳見[成本與保證金操作](docs/PINE_STRATEGY.md)。指標與策略仍分開下載。

1. 分別開啟最新版 [指標 Pine](candidates/8zz-history-latest.pine) 與 [策略 Pine](candidates/8zz-strategy-latest.pine)，按 Raw 複製各自的**完整內容**。兩份各自建立一個腳本，不要串接成同一檔案。
2. 在 TradingView 開啟 Pine Editor，備份舊腳本後以完整檔案取代內容。
3. 儲存、加入圖表／更新圖表，確認編譯成功與事件標籤。
4. 使用提醒者需重建提醒，才會採用新腳本。

**GitHub 更新不會自動同步至 TradingView。** 原作者的[指標頁面](https://tw.tradingview.com/script/6pVuUMS1/)仍保留供參考，但本分支新資料須自行更新腳本。

指標可使用30分鐘或1小時線；原生策略沿用標準30分鐘日盤設定，請依[策略操作](docs/PINE_STRATEGY.md)使用。重建成對檔案：`python scripts/history_completion.py report`（僅讀保存資料，不抓取、不呼叫AI）。

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


先前品質審查紀錄保留作歷史比較，並非目前情緒標準：[原9篇測試](docs/QUALITY_TEST_RESULTS.md)、[後續離線重驗](docs/QUALITY_RULE_REVIEW.md)。最新活躍判讀器是original_author.py；舊的強恐慌／指定關鍵字／標的與人工核圖門檻不供本批使用。原作者完整排除規則、強度及few-shot已保留。

專用手動入口已驗證（workflow ID410173704，固定PR ref）；PR未合併時若網頁無按鈕，可依[本批報告](docs/HISTORY_BATCH_01_RESULTS.md)的gh命令操作。同一batch已完成／5次耗盡，重啟不再生成，不能用舊Apify入口替代。
