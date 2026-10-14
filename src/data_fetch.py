"""Free price downloader: Yahoo v8 direct (no key) + gold-api live fallback."""
import pandas as pd
import requests
from config import DATA_DIR, DATA_H1_PATH, DATA_M15_PATH, DXY_SYMBOL, GOLD_SYMBOL

UA = {"User-Agent": "Mozilla/5.0"}
DXY_H1_PATH = DATA_DIR / "dxy_h1.csv"


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


def load_dxy() -> pd.DataFrame | None:
    try:
        if DXY_H1_PATH.exists():
            return pd.read_csv(DXY_H1_PATH, index_col=0, parse_dates=True)
    except Exception:
        pass
    return None


def update_all() -> None:
    h1 = fetch_yahoo(GOLD_SYMBOL, "60m", "1y")
    h1.to_csv(DATA_H1_PATH)
    print(f"H1 rows: {len(h1)} -> {DATA_H1_PATH} | last: {h1.index[-1]} close={h1['close'].iloc[-1]:.2f}")
    m15 = fetch_yahoo(GOLD_SYMBOL, "15m", "1mo")
    m15.to_csv(DATA_M15_PATH)
    print(f"M15 rows: {len(m15)} -> {DATA_M15_PATH}")
    try:
        dxy = fetch_yahoo(DXY_SYMBOL, "60m", "1y")
        dxy.to_csv(DXY_H1_PATH)
        print(f"DXY rows: {len(dxy)} -> {DXY_H1_PATH}")
    except Exception as e:
        print(f"DXY fetch failed (non-fatal): {e}")
    spot = live_spot()
    print(f"Live spot XAU: {spot}")


if __name__ == "__main__":
    update_all()
