"""Train LightGBM v2 (balanced, regularized, DXY-aware)."""
import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.metrics import classification_report
from config import DATA_H1_PATH, MODEL_PATH
from src.features import add_features, make_label, FEATURE_COLS


def train() -> dict:
    from src.data_fetch import load_dxy
    df = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
    df = add_features(df, load_dxy())
    df["label"] = make_label(df)
    df = df[df["label"] != 2].copy()
    X = df[FEATURE_COLS]
    y = df["label"]
    split = int(len(df) * 0.8)
    Xtr, Xte, ytr, yte = X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]
    model = lgb.LGBMClassifier(
        n_estimators=300, learning_rate=0.04, num_leaves=31,
        min_child_samples=60, reg_alpha=0.1, reg_lambda=1.0,
        class_weight="balanced", verbose=-1,
    )
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    print(classification_report(yte, pred, target_names=["SELL", "BUY"]))
    joblib.dump({"model": model, "features": FEATURE_COLS, "version": 2}, MODEL_PATH)
    print(f"Saved v2 -> {MODEL_PATH} ({len(df)} samples)")
    return {"train_rows": len(Xtr), "test_rows": len(Xte)}


if __name__ == "__main__":
    train()
