"""Paper-trade scoreboard: append fired signals, auto-mark TP1/SL outcomes.

Free, local CSV. check_signal.py logs; web displays. No broker, no-fill fiction:
outcome = first touch of SL vs TP1 on subsequent H1 candles.
"""
import pandas as pd
from config import DATA_DIR, DATA_H1_PATH

LOG = DATA_DIR / "signals_log.csv"
COLS = ["id", "time", "tf", "side", "entry", "sl", "tp1", "tp2", "tp3",
        "conf", "hist_conf", "outcome", "pips", "closed_at"]


def log_signal(sig: dict, tf: str) -> bool:
    if sig.get("side") == "WAIT" or not sig.get("sl"):
        return False
    sid = f"{tf}-{sig['time']}-{sig['side']}"
    try:
        log = pd.read_csv(LOG)
        if sid in log["id"].astype(str).values:
            return False
    except Exception:
        log = pd.DataFrame(columns=COLS)
    row = {"id": sid, "time": sig["time"], "tf": tf, "side": sig["side"],
           "entry": sig["price"], "sl": sig["sl"], "tp1": sig["tp1"],
           "tp2": sig.get("tp2"), "tp3": sig.get("tp3"), "conf": sig["confidence"],
           "hist_conf": sig.get("hist_conf", ""), "outcome": "OPEN",
           "pips": "", "closed_at": ""}
    log = pd.concat([log, pd.DataFrame([row])], ignore_index=True)
    log.to_csv(LOG, index=False)
    return True


def mark_outcomes() -> pd.DataFrame:
    try:
        log = pd.read_csv(LOG)
    except Exception:
        return pd.DataFrame(columns=COLS)
    if log.empty:
        return log
    try:
        h1 = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
    except Exception:
        return log
    for i, r in log[log["outcome"] == "OPEN"].iterrows():
        try:
            t = pd.to_datetime(r["time"], utc=True)
            fwd = h1[h1.index > t]
            if fwd.empty:
                continue
            if r["side"] == "BUY":
                sl_hit = fwd[fwd["low"] <= r["sl"]].index.min()
                tp_hit = fwd[fwd["high"] >= r["tp1"]].index.min()
                mult = 1
            else:
                sl_hit = fwd[fwd["high"] >= r["sl"]].index.min()
                tp_hit = fwd[fwd["low"] <= r["tp1"]].index.min()
                mult = -1
            if pd.isna(sl_hit) and pd.isna(tp_hit):
                continue
            if pd.isna(tp_hit) or (not pd.isna(sl_hit) and sl_hit <= tp_hit):
                log.at[i, "outcome"] = "SL"
                log.at[i, "pips"] = round(-abs(r["entry"] - r["sl"]) / 0.1, 0)
                log.at[i, "closed_at"] = str(sl_hit)
            else:
                log.at[i, "outcome"] = "TP1"
                log.at[i, "pips"] = round(abs(r["tp1"] - r["entry"]) / 0.1, 0)
                log.at[i, "closed_at"] = str(tp_hit)
        except Exception:
            continue
    log.to_csv(LOG, index=False)
    return log


def summary(log: pd.DataFrame) -> dict:
    closed = log[log["outcome"].isin(["TP1", "SL"])]
    return {
        "total": len(log), "open": int((log["outcome"] == "OPEN").sum()),
        "tp1": int((log["outcome"] == "TP1").sum()),
        "sl": int((log["outcome"] == "SL").sum()),
        "winrate": round((closed["outcome"] == "TP1").mean() * 100, 1) if len(closed) else 0,
        "net_pips": float(pd.to_numeric(closed["pips"], errors="coerce").fillna(0).sum()) if len(closed) else 0,
    }
