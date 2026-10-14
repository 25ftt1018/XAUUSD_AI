"""Ensure data + model exist (for fresh Cloud deploy where data/models are git-ignored)."""
from config import DATA_H1_PATH, MODEL_PATH


def ensure_ready() -> str:
    if MODEL_PATH.exists() and DATA_H1_PATH.exists():
        return "ready"
    from src.data_fetch import update_all
    from src.train import train
    if not DATA_H1_PATH.exists():
        update_all()
    if not MODEL_PATH.exists():
        train()
    return "bootstrapped"
