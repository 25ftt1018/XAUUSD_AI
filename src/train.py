"""Train LightGBM (small, free-tier friendly). Walk-forward evaluated."""
import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.metrics import classification_report
from config import DATA_H1_PATH, MODEL_PATH
from src.features import add_features, make_label, FEATURE_COLS


def train() -> dict:
    df = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
    df = add_features(df)
    df["label"] = make_label(df)
    # Keep only confident moves for training
    df = df[df["label"] != 2].copy()
    X = df[FEATURE_COLS]
    y = df["label"]
    split = int(len(df) * 0.8)
    Xtr, Xte, ytr, yte = X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]
    model = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=31, verbose=-1)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    print(classification_report(yte, pred, target_names=["SELL", "BUY"]))
    joblib.dump({"model": model, "features": FEATURE_COLS}, MODEL_PATH)
    print(f"Saved -> {MODEL_PATH} ({len(df)} samples)")
    return {"train_rows": len(Xtr), "test_rows": len(Xte)}


if __name__ == "__main__":
    train()
