"""Train M30 scalp model (ATR labels, validated walk-forward 3/3 folds green).

Params locked to validation: th=0.65, 3h hold, NO session gate.
Re-run walk-forward (see Temp/m30_sweep.py) before changing labels/threshold.
"""
import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.metrics import classification_report
from config import DATA_DIR, MODELS_DIR
from src.features import add_features, make_atr_label, FEATURE_COLS

M30_PATH = DATA_DIR / "xau_m30.csv"
MODEL_M30 = MODELS_DIR / "lgbm_m30.pkl"


def train_m30() -> dict:
    df = pd.read_csv(M30_PATH, index_col=0, parse_dates=True)
    df = add_features(df)  # DXY H1 index mismatch, skip like H4 v1
    df["label"] = make_atr_label(df, horizon=8, tp_mult=0.75, sl_mult=0.5)
    df = df[df["label"] != 2].copy()
    X, y = df[FEATURE_COLS], df["label"]
    split = int(len(df) * 0.8)
    Xtr, Xte, ytr, yte = X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]
    model = lgb.LGBMClassifier(
        n_estimators=300, learning_rate=0.04, num_leaves=31,
        min_child_samples=60, reg_alpha=0.1, reg_lambda=1.0,
        class_weight="balanced", random_state=42, deterministic=True, verbose=-1)
    model.fit(Xtr, ytr)
    print(classification_report(yte, model.predict(Xte), target_names=["SELL", "BUY"]))
    joblib.dump({"model": model, "features": FEATURE_COLS, "version": "m30-v1"}, MODEL_M30)
    print(f"Saved -> {MODEL_M30} ({len(df)} samples)")
    return {"train_rows": len(Xtr), "test_rows": len(Xte)}


if __name__ == "__main__":
    train_m30()
