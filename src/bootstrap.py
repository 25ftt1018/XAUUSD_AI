"""Ensure data + models exist (fresh Cloud deploy where data/models are git-ignored)."""
from config import DATA_DIR, DATA_H1_PATH, MODEL_PATH, MODELS_DIR


def ensure_ready() -> str:
    import time
    h4_path = DATA_DIR / "xau_h4.csv"
    h4_model = MODELS_DIR / "lgbm_h4.pkl"
    m30_path = DATA_DIR / "xau_m30.csv"
    m30_model = MODELS_DIR / "lgbm_m30.pkl"
    if MODEL_PATH.exists() and DATA_H1_PATH.exists() and h4_model.exists() and h4_path.exists():
        # Refresh stale data (>90 min) so Cloud signals don't freeze between reboots
        try:
            if time.time() - DATA_H1_PATH.stat().st_mtime > 90 * 60:
                from src.data_fetch import update_all
                update_all()
                return "refreshed"
        except Exception as e:
            print(f"Refresh skipped: {e}")
        if not m30_path.exists() or not m30_model.exists():
            try:
                from src.data_fetch import fetch_yahoo, resample_m30
                from config import GOLD_SYMBOL, DATA_M15_PATH
                if not m30_path.exists():
                    m15 = fetch_yahoo(GOLD_SYMBOL, "15m", "60d")
                    m15.to_csv(DATA_M15_PATH)
                    resample_m30(m15).to_csv(m30_path)
                if not m30_model.exists():
                    from src.train_m30 import train_m30
                    train_m30()
            except Exception as e:
                print(f"M30 bootstrap skipped: {e}")
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
    if not (DATA_DIR / "xau_m30.csv").exists() or not (MODELS_DIR / "lgbm_m30.pkl").exists():
        try:
            from config import DATA_M15_PATH
            if not (DATA_DIR / "xau_m30.csv").exists() and DATA_M15_PATH.exists():
                import pandas as pd
                from src.data_fetch import resample_m30
                m15 = pd.read_csv(DATA_M15_PATH, index_col=0, parse_dates=True)
                resample_m30(m15).to_csv(DATA_DIR / "xau_m30.csv")
            from src.train_m30 import train_m30
            train_m30()
        except Exception as e:
            print(f"M30 train skipped: {e}")
    return "bootstrapped"
