"""Live signal generation from latest candle."""
import pandas as pd
import joblib
from config import DATA_H1_PATH, MODEL_PATH, PROB_THRESHOLD, ATR_SL_MULT, TP1_R, TP2_R


def get_signal() -> dict:
    bundle = joblib.load(MODEL_PATH)
    model, feats = bundle["model"], bundle["features"]
    from src.features import add_features
    df = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
    df = add_features(df)
    last = df.iloc[[-1]]
    proba = model.predict_proba(last[feats])[0]  # [p_sell, p_buy]
    price = float(last["close"].iloc[0])
    atr = float(last["atr14"].iloc[0])
    p_sell, p_buy = float(proba[0]), float(proba[1])
    if p_buy >= PROB_THRESHOLD and p_buy > p_sell:
        side, conf = "BUY", p_buy
    elif p_sell >= PROB_THRESHOLD and p_sell > p_buy:
        side, conf = "SELL", p_sell
    else:
        side, conf = "WAIT", max(p_buy, p_sell)
    sl_dist = atr * ATR_SL_MULT
    if side == "BUY":
        sl, tp1, tp2 = price - sl_dist, price + sl_dist * TP1_R, price + sl_dist * TP2_R
    elif side == "SELL":
        sl, tp1, tp2 = price + sl_dist, price - sl_dist * TP1_R, price - sl_dist * TP2_R
    else:
        sl = tp1 = tp2 = None
    return {
        "side": side, "confidence": round(conf * 100, 1), "price": round(price, 2),
        "sl": round(sl, 2) if sl else None, "tp1": round(tp1, 2) if tp1 else None,
        "tp2": round(tp2, 2) if tp2 else None, "atr": round(atr, 2),
        "time": str(df.index[-1]),
    }


if __name__ == "__main__":
    print(get_signal())
