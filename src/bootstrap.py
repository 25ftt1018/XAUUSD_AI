"""Ensure data + models exist (fresh Cloud deploy where data/models are git-ignored)."""
from config import DATA_DIR, DATA_H1_PATH, MODEL_PATH, MODELS_DIR


def ensure_ready() -> str:
    import time
    h4_path = DATA_DIR / "xau_h4.csv"
    h4_model = MODELS_DIR / "lgbm_h4.pkl"
    if MODEL_PATH.exists() and DATA_H1_PATH.exists() and h4_model.exists() and h4_path.exists():
        # Refresh stale data (>90 min) so Cloud signals don't freeze between reboots
        try:
            if time.time() - DATA_H1_PATH.stat().st_mtime > 90 * 60:
                from src.data_fetch import update_all
                update_all()
                return "refreshed"
        except Exception as e:
            print(f"Refresh skipped: {e}")
        return "ready"
    from src.data_fetch import update_all
    if not DATA_H1_PATH.exists() or not h4_path.exists():
        update_all()
    try:
        from src.news import load_events
        load_events()
    except Exception as e:
        print(f"News calendar skipped: {e}")
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
