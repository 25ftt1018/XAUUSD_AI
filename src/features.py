"""Feature engineering: RSI, EMA, MACD, ATR, Bollinger + time/session."""
import pandas as pd
import numpy as np


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / (dn + 1e-9)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c = df["close"]
    df["ema20"] = c.ewm(span=20).mean()
    df["ema50"] = c.ewm(span=50).mean()
    df["ema_dist"] = (c - df["ema20"]) / df["ema20"] * 100
    df["rsi14"] = rsi(c)
    ema12 = c.ewm(span=12).mean()
    ema26 = c.ewm(span=26).mean()
    df["macd"] = ema12 - ema26
    df["macd_sig"] = df["macd"].ewm(span=9).mean()
    df["atr14"] = atr(df)
    df["atr_pct"] = df["atr14"] / c * 100
    mid = c.rolling(20).mean()
    sd = c.rolling(20).std()
    df["bb_pos"] = (c - mid) / (2 * sd + 1e-9)
    for n in (1, 3, 5):
        df[f"ret_{n}"] = c.pct_change(n) * 100
    df["vol_chg"] = df["volume"].pct_change().fillna(0)
    idx = pd.to_datetime(df.index, utc=True)
    df["hour"] = idx.hour
    df["dow"] = idx.dayofweek
    # London (7-10 UTC) / NY (12-16 UTC) killzones
    df["is_london"] = ((idx.hour >= 7) & (idx.hour <= 10)).astype(int)
    df["is_ny"] = ((idx.hour >= 12) & (idx.hour <= 16)).astype(int)
    return df.dropna()


FEATURE_COLS = [
    "ema_dist", "rsi14", "macd", "macd_sig", "atr_pct", "bb_pos",
    "ret_1", "ret_3", "ret_5", "vol_chg", "hour", "dow", "is_london", "is_ny",
]


def make_label(df: pd.DataFrame, horizon: int = 4, tp_pct: float = 0.4, sl_pct: float = 0.3) -> pd.Series:
    """Triple-barrier-lite: +tp% in `horizon` bars before -sl% => 1, opposite => 0, else 2 (no-trade)."""
    close = df["close"].values
    labels = np.full(len(df), 2)
    for i in range(len(df) - horizon):
        entry = close[i]
        fwd = close[i + 1 : i + 1 + horizon]
        up = ((fwd - entry) / entry * 100 >= tp_pct).any()
        dn = ((entry - fwd) / entry * 100 >= sl_pct).any()
        first_up = next((k for k, p in enumerate(fwd) if (p - entry) / entry * 100 >= tp_pct), 99)
        first_dn = next((k for k, p in enumerate(fwd) if (entry - p) / entry * 100 >= sl_pct), 99)
        if up and first_up < first_dn:
            labels[i] = 1
        elif dn and first_dn < first_up:
            labels[i] = 0
    return pd.Series(labels, index=df.index, name="label")
