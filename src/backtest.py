"""Backtest v2 with same gates as live signal."""
import pandas as pd
import joblib
from config import (
    DATA_H1_PATH, MODEL_PATH, PROB_THRESHOLD, PROB_STRONG,
    REQUIRE_SESSION, REQUIRE_TREND, ATR_MIN_PCT,
)
from src.features import add_features

SPREAD_PCT = 0.02


def backtest() -> dict:
    from src.data_fetch import load_dxy
    bundle = joblib.load(MODEL_PATH)
    model, feats = bundle["model"], bundle["features"]
    df = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
    df = add_features(df, load_dxy()).iloc[int(len(df) * 0.8):].copy()
    for c in feats:
        if c not in df.columns:
            df[c] = 0.0
    proba = model.predict_proba(df[feats])
    df["p_sell"], df["p_buy"] = proba[:, 0], proba[:, 1]
    trades = []
    for i in range(len(df) - 5):
        row = df.iloc[i]
        side = None
        conf = 0.0
        if row["p_buy"] >= PROB_THRESHOLD and row["p_buy"] > row["p_sell"]:
            side, conf = 1, row["p_buy"]
        elif row["p_sell"] >= PROB_THRESHOLD and row["p_sell"] > row["p_buy"]:
            side, conf = -1, row["p_sell"]
        if side is None:
            continue
        if row.get("atr_pct", 1) < ATR_MIN_PCT:
            continue
        if REQUIRE_SESSION and not row.get("in_session", 1) and conf < PROB_STRONG:
            continue
        if REQUIRE_TREND and side == 1 and row.get("trend", 0) < 0:
            continue
        if REQUIRE_TREND and side == -1 and row.get("trend", 0) > 0:
            continue
        entry = df["close"].iloc[i]
        exit_p = df["close"].iloc[i + 4]
        ret = (exit_p - entry) / entry * 100 * side - SPREAD_PCT
        trades.append(ret)
    s = pd.Series(trades)
    result = {
        "trades": len(s), "winrate": round((s > 0).mean() * 100, 1) if len(s) else 0,
        "avg_ret_pct": round(s.mean(), 3) if len(s) else 0,
        "total_ret_pct": round(s.sum(), 2) if len(s) else 0,
    }
    print(result)
    return result


if __name__ == "__main__":
    backtest()
