"""Free price downloader: Yahoo v8 direct (no key) + gold-api live fallback."""
import pandas as pd
import requests
from config import DATA_H1_PATH, DATA_M15_PATH

UA = {"User-Agent": "Mozilla/5.0"}


def fetch_yahoo(symbol: str = "GC=F", interval: str = "60m", rng: str = "1y") -> pd.DataFrame:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={rng}"
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    ts = pd.to_datetime(res["timestamp"], unit="s", utc=True)
    q = res["indicators"]["quote"][0]
    adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose", q["close"])
    df = pd.DataFrame({
        "time": ts, "open": q["open"], "high": q["high"],
        "low": q["low"], "close": adj or q["close"], "volume": q.get("volume", [0]*len(ts)),
    }).dropna().set_index("time").sort_index()
    return df


def live_spot() -> float | None:
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()["price"])
    except Exception:
        return None


def update_all() -> None:
    h1 = fetch_yahoo("GC=F", "60m", "1y")
    h1.to_csv(DATA_H1_PATH)
    print(f"H1 rows: {len(h1)} -> {DATA_H1_PATH} | last: {h1.index[-1]} close={h1['close'].iloc[-1]:.2f}")
    m15 = fetch_yahoo("GC=F", "15m", "1mo")
    m15.to_csv(DATA_M15_PATH)
    print(f"M15 rows: {len(m15)} -> {DATA_M15_PATH}")
    spot = live_spot()
    print(f"Live spot XAU: {spot}")


if __name__ == "__main__":
    update_all()
