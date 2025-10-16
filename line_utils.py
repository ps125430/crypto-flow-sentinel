import requests
import json

API_PUSH = "https://api.line.me/v2/bot/message/push"
API_MULTICAST = "https://api.line.me/v2/bot/message/multicast"
API_QUOTA_CONSUMPTION = "https://api.line.me/v2/bot/message/quota/consumption"

def _auth_headers(access_token: str):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

def push_text(access_token: str, user_id: str, text: str):
    body = {"to": user_id, "messages": [{"type": "text", "text": text[:4900]}]}
    r = requests.post(API_PUSH, headers=_auth_headers(access_token), data=json.dumps(body), timeout=15)
    r.raise_for_status()
    return True

def multicast_text(access_token: str, user_ids, text: str):
    body = {"to": user_ids, "messages": [{"type": "text", "text": text[:4900]}]}
    r = requests.post(API_MULTICAST, headers=_auth_headers(access_token), data=json.dumps(body), timeout=20)
    r.raise_for_status()
    return True

def push_flex_report(access_token: str, user_id: str, flex_bubble: dict):
    # flex_bubble is a full message object {type:flex, altText, contents}
    body = {"to": user_id, "messages": [flex_bubble]}
    r = requests.post(API_PUSH, headers=_auth_headers(access_token), data=json.dumps(body), timeout=20)
    r.raise_for_status()
    return True

def get_quota_consumption(access_token: str) -> int:
    r = requests.get(API_QUOTA_CONSUMPTION, headers=_auth_headers(access_token), timeout=10)
    if r.status_code == 200:
        data = r.json()
        return int(data.get("totalUsage", 0))
    return 0

def quota_warning(access_token: str, warn_percent: float) -> str | None:
    # We cannot fetch the monthly quota limit via this endpoint without a plan; treat 500 as a common free baseline.
    # Adjust this according to your plan.
    # For demonstration, assume 500 messages/month free.
    DEFAULT_MONTHLY_LIMIT = 500
    used = get_quota_consumption(access_token)
    percent = (used / DEFAULT_MONTHLY_LIMIT) * 100 if DEFAULT_MONTHLY_LIMIT else 0
    if percent >= warn_percent:
        return f"⚠️ 訊息用量接近上限：已用 {used}/{DEFAULT_MONTHLY_LIMIT}（{percent:.1f}%）。"
    return None
