import pytz
from datetime import datetime
import random

COINS = ["BTC", "ETH", "ADA", "SOL", "DOGE", "XRP"]

def fake_score():
    now = datetime.utcnow()
    rnd = random.Random(now.strftime("%Y%m%d%H"))
    return max(0, min(100, int(rnd.normalvariate(60, 20))))

def label(score):
    if score >= 70:
        return f"{score}（偏多）"
    if score >= 40:
        return f"{score}（區間）"
    return f"{score}（偏空）"

def build_report(tag: str = "", tzname: str = "Asia/Taipei") -> str:
    tz = pytz.timezone(tzname)
    now_local = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append(f"🔔 Crypto Flow Sentinel 報告（{tag}，{now_local}）")
    lines.append("")
    for c in COINS:
        s = fake_score()
        lines.append(f"{c}：{label(s)}")
    lines.append("")
    lines.append("📌 註：本訊息為系統化情緒＋技術指標的「分數草稿」。非投資建議。")
    return "\n".join(lines)

def build_flex_report(text_report: str):
    """
    Turn the text report into an array of Flex bubbles for richer display.
    Each bubble contains a section of the report.
    """
    # Simple split to avoid too-long messages
    chunks = []
    buf = []
    for line in text_report.splitlines():
        buf.append(line)
        if len("\n".join(buf)) > 900:
            chunks.append("\n".join(buf))
            buf = []
    if buf:
        chunks.append("\n".join(buf))

    bubbles = []
    for chunk in chunks:
        bubbles.append({
          "type": "flex",
          "altText": "Crypto Flow Sentinel 報告",
          "contents": {
            "type": "bubble",
            "body": {
              "type": "box",
              "layout": "vertical",
              "contents": [
                {"type": "text", "text": "Crypto Flow Sentinel", "weight": "bold", "size": "lg"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": chunk, "wrap": True, "margin": "md"}
              ]
            }
          }
        })
    return bubbles
