import os, json, threading

DB_PATH = os.environ.get("USER_DB_PATH", "users.json")
_lock = threading.Lock()

def load_user_ids():
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return list(dict.fromkeys([x for x in data if isinstance(x, str)]))
            return []
    except Exception:
        return []

def save_user_ids(ids):
    with _lock:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(ids, f, ensure_ascii=False, indent=2)

def add_user_id(user_id: str):
    ids = load_user_ids()
    if user_id not in ids:
        ids.append(user_id)
        save_user_ids(ids)
    return ids
