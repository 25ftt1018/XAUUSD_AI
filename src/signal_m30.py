"""M30 scalp signal (holds ~3h). Validated: th=0.65, NO session gate.

Walk-forward 3/3 folds green all-hours; session gate HURT M30 (starves sample
across 3h holds), so it is deliberately absent here. All other guards apply:
market-open, staleness, spot-deviation, news blackout.
"""
import pandas as pd
import joblib
from config import DATA_DIR, MODELS_DIR, ATR_SL_MULT

M30_PATH = DATA_DIR / "xau_m30.csv"
MODEL_M30 = MODELS_DIR / "lgbm_m30.pkl"
TH = 0.65
PIP = 0.1


def get_signal_m30() -> dict:
    bundle = joblib.load(MODEL_M30)
    model, feats = bundle["model"], bundle["features"]
    from src.features import add_features
    raw = pd.read_csv(M30_PATH, index_col=0, parse_dates=True)
    df = add_features(raw)
    candle_time = df.index[-1]
    from src.market import is_market_open, check_fresh, check_spot, MAX_AGE_M30_H, now_utc
    _now = now_utc()
    _open, _open_why = is_market_open(_now)
    _fresh, _fresh_why = check_fresh(candle_time, MAX_AGE_M30_H, _now)
    try:
        from src.data_fetch import live_spot
        _spot = live_spot()
    except Exception:
        _spot = None
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
    reason = f"M30 scalp model {conf*100:.1f}%"
    try:
        from src.news import status as news_status
        ns = news_status()
        if ns.get("blocked") and side != "WAIT":
            side = "WAIT"
            reason = f"⚠️ {ns['title']} ({ns['mins_to']:+.0f}min) — paused"
    except Exception:
        ns = {}
        reason = f"M30 scalp model {conf*100:.1f}%"
    try:
        from src.signal import _screener
        screener = _screener()
    except Exception:
        screener = {}
    from src.calibration import hist_conf
    base = {
        "side": side, "confidence": round(conf * 100, 1), "hist_conf": round(hist_conf(conf), 1), "price": round(price, 2),
        "sl": round(sl, 2) if sl else None, "tp1": round(tp1, 2) if tp1 else None,
        "tp2": round(tp2, 2) if tp2 else None, "tp3": round(tp3, 2) if tp3 else None,
        "atr": round(atr, 2), "time": str(df.index[-1]), "tf": "M30",
        "reason": reason, "reasons": [reason],
        "running_pips": 0.0, "peak_pips": 0.0, "screener": screener,
        "spot": round(float(_spot), 2) if _spot else None, "entry_source": "GC=F futures",
    }
    # Stale/closed-market and spot-deviation gates. NO session gate (validated: hurts M30).
    if side != "WAIT":
        if not _open:
            base["side"] = "WAIT"
            base["reason"] = f"⏸ {_open_why} — last M30 {candle_time}"
            base["reasons"] = [reason, base["reason"]]
        elif not _fresh:
            base["side"] = "WAIT"
            base["reason"] = f"⏸ {_fresh_why} — market may be closed"
            base["reasons"] = [reason, base["reason"]]
        else:
            _ok, _why = check_spot(price, _spot, atr)
            if not _ok:
                base["side"] = "WAIT"
                base["reason"] = f"⏸ {_why} — no trade"
                base["reasons"] = [reason, base["reason"]]
    if base["side"] == "WAIT":
        base["sl"] = base["tp1"] = base["tp2"] = base["tp3"] = None
    return base


if __name__ == "__main__":
    print(get_signal_m30())
