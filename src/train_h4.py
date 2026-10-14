"""Train H4 swing model (less noise than H1)."""
import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.metrics import classification_report
from config import DATA_DIR, MODELS_DIR
from src.features import add_features, make_label, FEATURE_COLS

H4_PATH = DATA_DIR / "xau_h4.csv"
MODEL_H4 = MODELS_DIR / "lgbm_h4.pkl"


def train_h4() -> dict:
    df = pd.read_csv(H4_PATH, index_col=0, parse_dates=True)
    df = add_features(df)  # DXY H1 index mismatch, skip for H4 v1
    df["label"] = make_label(df, horizon=6, tp_pct=0.8, sl_pct=0.6)
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
    joblib.dump({"model": model, "features": FEATURE_COLS, "version": "h4-v1"}, MODEL_H4)
    print(f"Saved -> {MODEL_H4} ({len(df)} samples)")
    return {"train_rows": len(Xtr), "test_rows": len(Xte)}


if __name__ == "__main__":
    train_h4()
