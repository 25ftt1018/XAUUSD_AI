"""Pre-news positioning bias (NOT a prediction). Combines trend + drift + DXY.

Outputs Bullish [BUY] / Bearish [SELL] / Neutral [WAIT] per upcoming event.
Honest accuracy ~50-53% (same as H4 model). Blackout still blocks real signals.
"""
import pandas as pd
import joblib
from config import DATA_DIR, DATA_H1_PATH, MODELS_DIR


def current_bias() -> dict:
    votes, why = 0, []
    # 1. H4 model
    try:
        from src.signal_h4 import get_signal_h4
        s = get_signal_h4()
        if s["side"] == "BUY":
            votes += 2; why.append("H4 BUY")
        elif s["side"] == "SELL":
            votes -= 2; why.append("H4 SELL")
        else:
            why.append(f"H4 WAIT {s['confidence']}%")
    except Exception as e:
        why.append(f"H4 n/a ({e})")
    # 2. 24h gold drift
    try:
        df = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
        drift = (df["close"].iloc[-1] - df["close"].iloc[-24]) / df["close"].iloc[-24] * 100
        if drift > 0.15:
            votes += 1; why.append(f"24h +{drift:.2f}%")
        elif drift < -0.15:
            votes -= 1; why.append(f"24h {drift:.2f}%")
        else:
            why.append(f"24h flat {drift:+.2f}%")
        # 3. RSI/EMA
        from src.features import add_features
        f = add_features(df).iloc[-1]
        if f["rsi14"] > 55 and f["trend"] > 0:
            votes += 1; why.append(f"RSI {f['rsi14']:.0f} + above EMA50")
        elif f["rsi14"] < 45 and f["trend"] < 0:
            votes -= 1; why.append(f"RSI {f['rsi14']:.0f} + below EMA50")
    except Exception as e:
        why.append(f"tech n/a ({e})")
    # 4. DXY (inverse: strong dollar = gold headwind)
    try:
        from src.data_fetch import load_dxy
        d = load_dxy()
        chg = (d["close"].iloc[-1] - d["close"].iloc[-24]) / d["close"].iloc[-24] * 100
        if chg > 0.1:
            votes -= 1; why.append(f"DXY +{chg:.2f}% headwind")
        elif chg < -0.1:
            votes += 1; why.append(f"DXY {chg:.2f}% tailwind")
    except Exception:
        pass
    if votes >= 2:
        label, action = ("Bullish (confirmed)", "BUY") if votes >= 3 else ("Bullish (weak)", "BUY")
    elif votes <= -2:
        label, action = ("Bearish (confirmed)", "SELL") if votes <= -3 else ("Bearish (weak)", "SELL")
    elif votes == 1:
        label, action = "Bullish (weak)", "BUY"
    elif votes == -1:
        label, action = "Bearish (weak)", "SELL"
    else:
        label, action = "Neutral", "WAIT"
    return {"label": label, "action": action, "votes": votes, "why": why}
