"""Simple backtest with spread cost, walk-forward style."""
import pandas as pd
import joblib
from config import DATA_H1_PATH, MODEL_PATH, PROB_THRESHOLD
from src.features import add_features, FEATURE_COLS

SPREAD_PCT = 0.02  # ~0.02% ~ $0.5 on $2500 gold


def backtest() -> dict:
    bundle = joblib.load(MODEL_PATH)
    model, feats = bundle["model"], bundle["features"]
    df = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
    df = add_features(df).iloc[int(len(df) * 0.8):].copy()
    proba = model.predict_proba(df[feats])
    df["p_sell"], df["p_buy"] = proba[:, 0], proba[:, 1]
    trades = []
    for i in range(len(df) - 5):
        row = df.iloc[i]
        side = None
        if row["p_buy"] >= PROB_THRESHOLD:
            side = 1
        elif row["p_sell"] >= PROB_THRESHOLD:
            side = -1
        if side is None:
            continue
        entry = df["close"].iloc[i]
        exit_p = df["close"].iloc[i + 4]  # hold 4H
        ret = (exit_p - entry) / entry * 100 * side - SPREAD_PCT
        trades.append(ret)
    s = pd.Series(trades)
    wins = (s > 0).sum()
    result = {
        "trades": len(s), "winrate": round(wins / len(s) * 100, 1) if len(s) else 0,
        "avg_ret_pct": round(s.mean(), 3) if len(s) else 0,
        "total_ret_pct": round(s.sum(), 2) if len(s) else 0,
    }
    print(result)
    return result


if __name__ == "__main__":
    backtest()
