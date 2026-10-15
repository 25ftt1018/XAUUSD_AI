"""Cron job: refresh data -> H1 + H4 signals -> telegram + scoreboard log."""
import argparse
import os
import warnings
# Silence joblib/loky physical-core probe noise on Windows cron runs.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count() or 4))
warnings.filterwarnings("ignore", message=".*LOKY_MAX_CPU_COUNT.*")
from src.bootstrap import ensure_ready
from src.signal import get_signal
from src.telegram_send import send, format_signal
from src.scoreboard import log_signal


def _h4():
    try:
        from src.signal_h4 import get_signal_h4
        return get_signal_h4()
    except Exception as e:
        print(f"H4 skipped: {e}")
        return {"side": "WAIT", "confidence": 0.0, "price": 0.0, "sl": None,
                "tp1": None, "tp2": None, "tp3": None, "reason": "H4 unavailable",
                "reasons": [], "time": "-", "screener": {}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="send even on WAIT (for testing)")
    args = ap.parse_args()
    ensure_ready()
    from src.data_fetch import update_all
    update_all()
    from src.market import is_market_open
    _open, _open_why = is_market_open()
    if not _open and not args.force:
        print(f"{_open_why} -> no push (market closed, avoids stale signals)")
        raise SystemExit(0)
    from config import MAX_SIGNALS_PER_DAY
    from src.scoreboard import count_today
    s = get_signal()
    print("H1:", s)
    h4 = _h4()
    print("H4:", h4)
    for sig, tag in ((h4, "H4 SWING"), (s, "H1")):
        if sig["side"] != "WAIT" or args.force:
            if sig["side"] != "WAIT" and not args.force:
                if count_today() >= MAX_SIGNALS_PER_DAY:
                    print(f"Daily cap {MAX_SIGNALS_PER_DAY} hit -> skip {tag} push")
                    continue
                is_new = log_signal(sig, tag)
                if not is_new:
                    print(f"Duplicate {tag} {sig['time']} {sig['side']} -> skip push")
                    continue
            msg = format_signal(sig).replace("XAUUSD", f"XAUUSD [{tag}]", 1)
            send(msg)
    if s["side"] == "WAIT" and h4["side"] == "WAIT" and not args.force:
        print("WAIT -> no push (avoids spam)")
