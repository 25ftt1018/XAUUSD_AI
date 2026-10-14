"""Ensure data + models exist (fresh Cloud deploy where data/models are git-ignored)."""
from config import DATA_DIR, DATA_H1_PATH, MODEL_PATH, MODELS_DIR


def ensure_ready() -> str:
    h4_path = DATA_DIR / "xau_h4.csv"
    h4_model = MODELS_DIR / "lgbm_h4.pkl"
    if MODEL_PATH.exists() and DATA_H1_PATH.exists() and h4_model.exists() and h4_path.exists():
        return "ready"
    from src.data_fetch import update_all
    if not DATA_H1_PATH.exists() or not h4_path.exists():
        update_all()
    if not MODEL_PATH.exists():
        from src.train import train
        train()
    if not h4_model.exists():
        try:
            from src.train_h4 import train_h4
            train_h4()
        except Exception as e:
            print(f"H4 train skipped: {e}")
    return "bootstrapped"
