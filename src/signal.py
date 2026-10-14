"""Live signal v3: card-ready (TP3, pips, HA + screener reasons)."""
import pandas as pd
import joblib
from config import (
    DATA_H1_PATH, DATA_M15_PATH, MODEL_PATH, PROB_THRESHOLD, PROB_STRONG,
    ATR_SL_MULT, TP1_R, TP2_R, REQUIRE_SESSION, REQUIRE_TREND, ATR_MIN_PCT,
)

PIP = 0.1  # XAUUSD: 10 pips = $1
TP3_R = 3.0


def _ha_last(df: pd.DataFrame) -> str:
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    ha_c = (o + h + l + c) / 4
    ha_o = (o.shift(1) + c.shift(1)) / 2
    ha_o.iloc[0] = o.iloc[0]
    bull = bool(ha_c.iloc[-1] > ha_o.iloc[-1])
    return "HA Bull Candle" if bull else "HA Bear Candle"


def _screener() -> dict:
    """M15/H1/DXY mini-bias for the right-side screener panel."""
    out = {}
    try:
        m15 = pd.read_csv(DATA_M15_PATH, index_col=0, parse_dates=True)
        c = m15["close"]
        out["M15"] = "BULL" if c.iloc[-1] > c.ewm(span=50).mean().iloc[-1] else "BEAR"
    except Exception:
        out["M15"] = "—"
    try:
        h1 = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
        c = h1["close"]
        out["H1"] = "BULL" if c.iloc[-1] > c.ewm(span=50).mean().iloc[-1] else "BEAR"
    except Exception:
        out["H1"] = "—"
    try:
        from src.data_fetch import load_dxy
        d = load_dxy()
        if d is not None and len(d) > 5:
            chg = (d["close"].iloc[-1] - d["close"].iloc[-4]) / d["close"].iloc[-4] * 100
            out["DXY"] = "UP (gold headwind)" if chg > 0 else "DOWN (gold tailwind)"
        else:
            out["DXY"] = "—"
    except Exception:
        out["DXY"] = "—"
    return out


def get_signal() -> dict:
    # News blackout first (cheap, before model load)
    try:
        from src.news import status as news_status
        ns = news_status()
    except Exception:
        ns = {"blocked": False}
    bundle = joblib.load(MODEL_PATH)
    model, feats = bundle["model"], bundle["features"]
    from src.features import add_features
    from src.data_fetch import load_dxy
    raw = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
    df = add_features(raw, load_dxy())
    last = df.iloc[[-1]].copy()
    for c in feats:
        if c not in last.columns:
            last[c] = 0.0
    proba = model.predict_proba(last[feats])[0]
    price = float(last["close"].iloc[0])
    atr = float(last["atr14"].iloc[0])
    atr_pct = float(last["atr_pct"].iloc[0])
    rsi = float(last["rsi14"].iloc[0])
    macd = float(last["macd"].iloc[0])
    macd_sig = float(last["macd_sig"].iloc[0])
    trend = float(last["trend"].iloc[0]) if "trend" in last else 0
    in_session = int(last["in_session"].iloc[0]) if "in_session" in last else 1
    p_sell, p_buy = float(proba[0]), float(proba[1])

    if p_buy >= PROB_THRESHOLD and p_buy > p_sell:
        side, conf = "BUY", p_buy
    elif p_sell >= PROB_THRESHOLD and p_sell > p_buy:
        side, conf = "SELL", p_sell
    else:
        side, conf = "WAIT", max(p_buy, p_sell)
    reason = f"model {conf*100:.1f}%"

    if side != "WAIT":
        if atr_pct < ATR_MIN_PCT:
            side, reason = "WAIT", f"low volatility ATR {atr_pct:.2f}% < {ATR_MIN_PCT}%"
        elif REQUIRE_SESSION and not in_session and conf < PROB_STRONG:
            side, reason = "WAIT", "outside London/NY session"
        elif REQUIRE_TREND and side == "BUY" and trend < 0:
            side, reason = "WAIT", "BUY blocked: below EMA50"
        elif REQUIRE_TREND and side == "SELL" and trend > 0:
            side, reason = "WAIT", "SELL blocked: above EMA50"

    sl_dist = atr * ATR_SL_MULT
    if side == "BUY":
        sl = price - sl_dist
        tp1, tp2, tp3 = price + sl_dist * TP1_R, price + sl_dist * TP2_R, price + sl_dist * TP3_R
    elif side == "SELL":
        sl = price + sl_dist
        tp1, tp2, tp3 = price - sl_dist * TP1_R, price - sl_dist * TP2_R, price - sl_dist * TP3_R
    else:
        sl = tp1 = tp2 = tp3 = None

    # News blackout overrides everything (can't predict CPI/FOMC/NFP direction)
    if ns.get("blocked") and side != "WAIT":
        side = "WAIT"
        reason = f"⚠️ {ns['title']} ({ns['mins_to']:+.0f}min) — paused"

    # Running / peak pips from last 5 bars vs entry (fresh signal => ~0)
    try:
        look = df["close"].iloc[-6:-1] if len(df) > 6 else df["close"].iloc[:-1]
        if side == "BUY":
            running = (price - price) / PIP
            mfe = ((look.max() - price) / PIP) if len(look) else 0.0
        elif side == "SELL":
            running = 0.0
            mfe = ((price - look.min()) / PIP) if len(look) else 0.0
        else:
            running, mfe = 0.0, 0.0
    except Exception:
        running, mfe = 0.0, 0.0

    reasons = []
    try:
        reasons.append(_ha_last(raw))
    except Exception:
        pass
    if side == "BUY":
        reasons.append("Momentum BUY" if (rsi > 50 and macd > macd_sig) else "Model BUY")
    elif side == "SELL":
        reasons.append("Momentum SELL" if (rsi < 50 and macd < macd_sig) else "Model SELL")
    else:
        reasons.append("No momentum edge")
    reasons.append(f"RSI {rsi:.0f} • {'Above' if trend > 0 else 'Below'} EMA50")
    reasons.append(reason)
    from src.calibration import hist_conf
    hc = round(hist_conf(conf), 1)

    return {
        "side": side, "confidence": round(conf * 100, 1), "hist_conf": hc, "price": round(price, 2),
        "sl": round(sl, 2) if sl else None, "tp1": round(tp1, 2) if tp1 else None,
        "tp2": round(tp2, 2) if tp2 else None, "tp3": round(tp3, 2) if tp3 else None,
        "atr": round(atr, 2), "time": str(df.index[-1]), "reason": reason,
        "reasons": reasons, "running_pips": round(float(running), 0),
        "peak_pips": round(float(max(mfe, 0)), 0), "screener": _screener(),
    }


if __name__ == "__main__":
    print(get_signal())
