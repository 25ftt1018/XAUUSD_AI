"""H4 swing signal (holds ~24h)."""
import pandas as pd
import joblib
from config import DATA_DIR, MODELS_DIR, ATR_SL_MULT

H4_PATH = DATA_DIR / "xau_h4.csv"
MODEL_H4 = MODELS_DIR / "lgbm_h4.pkl"
TH = 0.60
PIP = 0.1


def get_signal_h4() -> dict:
    bundle = joblib.load(MODEL_H4)
    model, feats = bundle["model"], bundle["features"]
    from src.features import add_features
    raw = pd.read_csv(H4_PATH, index_col=0, parse_dates=True)
    df = add_features(raw)
    last = df.iloc[[-1]].copy()
    for c in feats:
        if c not in last.columns:
            last[c] = 0.0
    proba = model.predict_proba(last[feats])[0]
    price = float(last["close"].iloc[0])
    atr = float(last["atr14"].iloc[0])
    p_sell, p_buy = float(proba[0]), float(proba[1])
    if p_buy >= TH and p_buy > p_sell:
        side, conf = "BUY", p_buy
    elif p_sell >= TH and p_sell > p_buy:
        side, conf = "SELL", p_sell
    else:
        side, conf = "WAIT", max(p_buy, p_sell)
    sl_dist = atr * ATR_SL_MULT
    if side == "BUY":
        sl, tp1, tp2, tp3 = price - sl_dist, price + sl_dist, price + sl_dist * 2, price + sl_dist * 3
    elif side == "SELL":
        sl, tp1, tp2, tp3 = price + sl_dist, price - sl_dist, price - sl_dist * 2, price - sl_dist * 3
    else:
        sl = tp1 = tp2 = tp3 = None
    reason = f"H4 swing model {conf*100:.1f}%"
    try:
        from src.news import status as news_status
        ns = news_status()
        if ns.get("blocked") and side != "WAIT":
            side = "WAIT"
            reason = f"⚠️ {ns['title']} ({ns['mins_to']:+.0f}min) — paused"
    except Exception:
        ns = {}
        reason = f"H4 swing model {conf*100:.1f}%"
    try:
        from src.signal import _screener
        screener = _screener()
    except Exception:
        screener = {}
    return {
        "side": side, "confidence": round(conf * 100, 1), "price": round(price, 2),
        "sl": round(sl, 2) if sl else None, "tp1": round(tp1, 2) if tp1 else None,
        "tp2": round(tp2, 2) if tp2 else None, "tp3": round(tp3, 2) if tp3 else None,
        "atr": round(atr, 2), "time": str(df.index[-1]), "tf": "H4",
        "reason": reason, "reasons": [reason],
        "running_pips": 0.0, "peak_pips": 0.0, "screener": screener,
    }


if __name__ == "__main__":
    print(get_signal_h4())
