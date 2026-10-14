"""Central config for Plan A (100% free)."""
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Free data sources (no key needed)
# GC=F = gold futures (XAUUSD proxy), DX-Y.NYB = dollar index
GOLD_SYMBOL = "GC=F"
DXY_SYMBOL = "DX-Y.NYB"

TIMEFRAMES = {
    "M15": "15m",
    "H1": "60m",
}

MODEL_PATH = MODELS_DIR / "lgbm_h1.pkl"
DATA_H1_PATH = DATA_DIR / "xau_h1.csv"
DATA_M15_PATH = DATA_DIR / "xau_m15.csv"

# Signal rules
PROB_THRESHOLD = 0.65
ATR_SL_MULT = 1.5
TP1_R = 1.0
TP2_R = 2.0
MAX_SIGNALS_PER_DAY = 3
