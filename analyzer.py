# analyzer.py
import os, time, requests
from datetime import datetime, timezone

ENABLE_CRYPTO = os.environ.get("ENABLE_CRYPTO", "1") == "1"
ENABLE_EQUITY = os.environ.get("ENABLE_EQUITY", "1") == "1"
ALPHA_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

COINS = ["bitcoin","ethereum","cardano","ripple","dogecoin","solana"]
COIN_SYMBOL = {"bitcoin":"BTC","ethereum":"ETH","cardano":"ADA","ripple":"XRP","dogecoin":"DOGE","solana":"SOL"}

STOCKS = ["MSFT","AAPL","NVDA","GOOGL","AMZN","META","TSLA","AMD","INTC","PLTR"]

def _get_json(url, params=None, timeout=12):
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _crypto_snapshot():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency":"usd","ids":",".join(COINS),"price_change_percentage":"1h,24h,7d"}
    data = _get_json(url, params)
    out = []
    for d in data:
        sym = COIN_SYMBOL.get(d["id"], d["symbol"].upper())
        score = _score_crypto(d)
        out.append({
            "symbol": sym,
            "price": d.get("current_price"),
            "ch1h": d.get("price_change_percentage_1h_in_currency"),
            "ch24h": d.get("price_change_percentage_24h_in_currency"),
            "ch7d": d.get("price_change_percentage_7d_in_currency"),
            "score": score
        })
    # 依分數排序
    out.sort(key=lambda x: (x["score"], x["ch24h"] or 0), reverse=True)
    return out

def _score_crypto(d):
    # 簡單版分數：24h 漲幅 + (1h*0.5) + 7d*0.3，壓到 0~100
    ch24 = d.get("price_change_percentage_24h_in_currency") or 0.0
    ch1  = d.get("price_change_percentage_1h_in_currency") or 0.0
    ch7  = d.get("price_change_percentage_7d_in_currency") or 0.0
    raw = ch24 + 0.5*ch1 + 0.3*ch7
    # 線性壓縮：-15~+15 映射到 0~100
    lo, hi = -15.0, 15.0
    x = 0 if raw <= lo else (100 if raw >= hi else (raw - lo) / (hi - lo) * 100)
    return int(round(x))

def _equity_snapshot():
    if not ALPHA_KEY:
        return []
    url = "https://www.alphavantage.co/query"
    out = []
    for sym in STOCKS:
        params = {"function":"TIME_SERIES_DAILY_ADJUSTED","symbol":sym,"apikey":ALPHA_KEY,"outputsize":"compact"}
        try:
            j = _get_json(url, params)
            series = j.get("Time Series (Daily)", {}) or j.get("Time Series Daily", {})
            if not series: 
                continue
            dates = sorted(series.keys(), reverse=True)
            if len(dates) < 2: 
                continue
            d0, d1 = dates[0], dates[1]
            c0 = float(series[d0]["4. close"]); c1 = float(series[d1]["4. close"])
            ch = (c0 - c1) / c1 * 100.0
            score = _score_equity(ch)
            out.append({"symbol": sym, "close": c0, "ch1d": ch, "score": score})
            time.sleep(0.2)  # 簡單節流
        except Exception:
            # 超額或暫失敗時，略過該標的
            pass
    out.sort(key=lambda x: (x["score"], x["ch1d"]), reverse=True)
    return out

def _score_equity(ch1d):
    # 以日變動粗略映射 0~100（-5%~+5% 範圍）
    lo, hi = -5.0, 5.0
    x = 0 if ch1d <= lo else (100 if ch1d >= hi else (ch1d - lo) / (hi - lo) * 100)
    return int(round(x))

def _fmt_pct(v, digits=1):
    if v is None: return "—"
    return f"{v:+.{digits}f}%"

def build_report(tag="即時", tzname="Asia/Taipei"):
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    lines = [f"🧭 Crypto Flow Sentinel — {tag} 報告（{now}）"]

    # Crypto
    if ENABLE_CRYPTO:
        try:
            c = _crypto_snapshot()
            if c:
                lines.append("\n💰 加密（1h/24h/7d）")
                row = []
                for it in c[:4]:  # 前四個精簡顯示
                    row.append(f"{it['symbol']} {it['score']:02d}｜{_fmt_pct(it['ch1h'])}/{_fmt_pct(it['ch24h'])}/{_fmt_pct(it['ch7d'])}")
                lines.append(" / ".join(row))
                # 潛力觀察（前 3）
                watch = ", ".join([f"{it['symbol']}" for it in c[:3]])
                lines.append(f"🔥 潛力觀察：{watch}")
        except Exception:
            lines.append("💰 加密：資料暫時不可用（API 限制或網路）")

    # Equities
    if ENABLE_EQUITY:
        try:
            e = _equity_snapshot()
            if e:
                lines.append("\n📈 美股（前一交易日）")
                row = []
                for it in e[:4]:
                    row.append(f"{it['symbol']} {it['score']:02d}｜{_fmt_pct(it['ch1d'])}")
                lines.append(" / ".join(row))
        except Exception:
            lines.append("📈 美股：資料暫時不可用（API 限制或網路）")

    # 總結
    concl = []
    if ENABLE_CRYPTO:
        concl.append("加密：看前 3 強勢，防追高")
    if ENABLE_EQUITY:
        concl.append("美股：關注半導體/巨科龍頭")
    if concl:
        lines.append("\n結論：" + "；".join(concl) + "。")

    return "\n".join(lines)

