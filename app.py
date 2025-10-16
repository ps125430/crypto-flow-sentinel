import os
import json
import hmac
import hashlib
import base64
import pytz
import logging
from datetime import datetime
from flask import Flask, request, jsonify, abort
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from line_utils import push_text, multicast_text, push_flex_report, get_quota_consumption, quota_warning
from storage import load_user_ids, add_user_id
from analyzer import build_report, build_flex_report

# --- Configuration ---
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Taipei")
QUOTA_WARN_PERCENT = float(os.environ.get("QUOTA_WARN_PERCENT", "80"))  # 80% default

if not CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("Missing env: LINE_CHANNEL_ACCESS_TOKEN")
if not CHANNEL_SECRET:
    raise RuntimeError("Missing env: LINE_CHANNEL_SECRET")

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

tz = pytz.timezone(TIMEZONE)
scheduler = BackgroundScheduler(timezone=tz)

def scheduled_job(tag):
    try:
        # Quota guard
        warn_msg = quota_warning(CHANNEL_ACCESS_TOKEN, QUOTA_WARN_PERCENT)
        report_text = build_report(tag=tag, tzname=TIMEZONE)
        user_ids = load_user_ids()
        if not user_ids:
            app.logger.warning("No user IDs to push yet.")
            return
        # Prefer Flex
        multicast_text(CHANNEL_ACCESS_TOKEN, user_ids, report_text)
        # Optionally follow up with Flex UI
        flex = build_flex_report(report_text)
        for chunk in flex:  # break into chunks of 10 messages if needed
            for uid in user_ids:
                push_flex_report(CHANNEL_ACCESS_TOKEN, uid, chunk)
        if warn_msg:
            for uid in user_ids:
                push_text(CHANNEL_ACCESS_TOKEN, uid, warn_msg)
        app.logger.info(f"Pushed report ({tag}) to {len(user_ids)} users.")
    except Exception as e:
        app.logger.exception(f"Scheduled job failed: {e}")

# Four daily jobs (Taipei)
scheduler.add_job(scheduled_job, CronTrigger(hour=9, minute=0), kwargs={"tag": "09:00"})
scheduler.add_job(scheduled_job, CronTrigger(hour=15, minute=0), kwargs={"tag": "15:00"})
scheduler.add_job(scheduled_job, CronTrigger(hour=20, minute=30), kwargs={"tag": "20:30"})
scheduler.add_job(scheduled_job, CronTrigger(hour=0, minute=0), kwargs={"tag": "00:00"})
scheduler.start()

def verify_signature(request_body: bytes, signature: str) -> bool:
    mac = hmac.new(CHANNEL_SECRET.encode('utf-8'), msg=request_body, digestmod=hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode('utf-8')
    return hmac.compare_digest(expected, signature or "")

@app.post("/callback")
def callback():
    # Verify X-Line-Signature
    raw = request.get_data()
    sig = request.headers.get("X-Line-Signature", "")
    if not verify_signature(raw, sig):
        app.logger.warning("Invalid signature")
        return ("signature error", 400)

    body = request.get_json(force=True, silent=True) or {}
    events = body.get("events", [])
    for ev in events:
        etype = ev.get("type")
        source = ev.get("source", {})
        user_id = source.get("userId")

        if etype == "follow" and user_id:
            add_user_id(user_id)
            push_text(CHANNEL_ACCESS_TOKEN, user_id, "已訂閱 Crypto Flow Sentinel ✅\n每日 09:00 / 15:00 / 20:30 / 00:00 推送分析。")

        if etype == "message" and ev.get("message", {}).get("type") == "text" and user_id:
            text = ev["message"]["text"].strip().lower()
            if text in ("report", "r", "報告", "幫我看盤"):
                # Ack then compute
                push_text(CHANNEL_ACCESS_TOKEN, user_id, "⏳ 已接收，正在分析…")
                report_text = build_report(tag="即時", tzname=TIMEZONE)
                warn_msg = quota_warning(CHANNEL_ACCESS_TOKEN, QUOTA_WARN_PERCENT)
                # Send text and flex
                push_text(CHANNEL_ACCESS_TOKEN, user_id, report_text)
                for bubble in build_flex_report(report_text):
                    push_flex_report(CHANNEL_ACCESS_TOKEN, user_id, bubble)
                if warn_msg:
                    push_text(CHANNEL_ACCESS_TOKEN, user_id, warn_msg)
            elif text in ("stop", "退訂", "unsubscribe"):
                push_text(CHANNEL_ACCESS_TOKEN, user_id, "目前停用請封鎖官方帳號或聯絡管理者移除。")
            else:
                push_text(CHANNEL_ACCESS_TOKEN, user_id, "指令：\n- report / 報告：取得即時多空分數\n- 退訂：停止推送")
    return jsonify({"ok": True})

@app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
