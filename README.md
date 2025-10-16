# Crypto Flow Sentinel — LINE Messaging API 進階版（含簽名驗證／Flex／額度提醒）

> 台北時間 **09:00 / 15:00 / 20:30 / 00:00** 自動推播六大幣種多空分數；支援 Flex 視覺化訊息、X-Line-Signature 驗證、訊息配額提醒。

## ✅ 本專案加入
- ✅ **X-Line-Signature 驗證**（`app.py` → `verify_signature`）
- ✅ **Flex Message** 報告（`analyzer.build_flex_report` + `line_utils.push_flex_report`）
- ✅ **訊息額度提醒**：呼叫 `GET /v2/bot/message/quota/consumption`，達閾值（預設 80%）自動推送警示
- ✅ **即時指令**：使用者輸入 `report/報告` → 先回 `⏳ 正在分析…`，再送報告

## 🚀 快速部署
1. 於 LINE Developers 建立 **Messaging API** 頻道，取得：
   - `LINE_CHANNEL_ACCESS_TOKEN`（長期版）
   - `LINE_CHANNEL_SECRET`
2. 設定環境變數：
   - `LINE_CHANNEL_ACCESS_TOKEN`、`LINE_CHANNEL_SECRET`
   - `TIMEZONE=Asia/Taipei`
   - `QUOTA_WARN_PERCENT=80`（可選）
3. 部署（Replit / Render / Railway / Heroku 類皆可）：
   ```bash
   pip install -r requirements.txt
   gunicorn app:app
   ```
4. 在 LINE Developers Console → Messaging API：
   - 開啟 **Webhook**
   - Webhook URL 設為 `https://你的網域/callback`
5. 用戶加入你的官方帳號即可被記錄（`users.json`）。

## 🔧 替換分析邏輯（重要）
- 目前 `analyzer.py` 使用假分數。請替換為：
  - 交易所 API 抓 K 線（1h、4h、1d）
  - 計算 MA/RSI/布林、Funding、OI 等
  - 融合權重輸出 0–100 分與標籤。

## 🧪 測試
- 本機：
  ```bash
  export LINE_CHANNEL_ACCESS_TOKEN="你的token"
  export LINE_CHANNEL_SECRET="你的secret"
  python app.py
  # http://localhost:8080/healthz → ok
  ```
- 使用者傳 `report` → 機器人回「正在分析…」→ 報告（文字 + Flex）。

## 🔒 注意
- 請務必使用 **長期版** Channel Access Token；不要硬寫在程式碼。
- 配額計算：本專案用 500 則/月作為示範上限，請依你的官方帳號方案調整 `line_utils.quota_warning`。

---

Made for 綠茶。保持紀律、擁抱機率。
