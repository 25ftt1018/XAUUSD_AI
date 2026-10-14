"""Live signal v2 with session / trend / volatility gates."""
import pandas as pd
import joblib
from config import (
    DATA_H1_PATH, MODEL_PATH, PROB_THRESHOLD, PROB_STRONG,
    ATR_SL_MULT, TP1_R, TP2_R, REQUIRE_SESSION, REQUIRE_TREND, ATR_MIN_PCT,
)


def get_signal() -> dict:
    bundle = joblib.load(MODEL_PATH)
    model, feats = bundle["model"], bundle["features"]
    from src.features import add_features
    from src.data_fetch import load_dxy
    df = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
    df = add_features(df, load_dxy())
    last = df.iloc[[-1]]
    # Back-compat: v1 model lacks new cols
    for c in feats:
        if c not in last.columns:
            last[c] = 0.0
    proba = model.predict_proba(last[feats])[0]
    price = float(last["close"].iloc[0])
    atr = float(last["atr14"].iloc[0])
    atr_pct = float(last["atr_pct"].iloc[0])
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

    # Gates (strong signals bypass session gate only)
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
        sl, tp1, tp2 = price - sl_dist, price + sl_dist * TP1_R, price + sl_dist * TP2_R
    elif side == "SELL":
        sl, tp1, tp2 = price + sl_dist, price - sl_dist * TP1_R, price - sl_dist * TP2_R
    else:
        sl = tp1 = tp2 = None
        conf = max(p_buy, p_sell)
    return {
        "side": side, "confidence": round(conf * 100, 1), "price": round(price, 2),
        "sl": round(sl, 2) if sl else None, "tp1": round(tp1, 2) if tp1 else None,
        "tp2": round(tp2, 2) if tp2 else None, "atr": round(atr, 2),
        "time": str(df.index[-1]), "reason": reason,
    }


if __name__ == "__main__":
    print(get_signal())
