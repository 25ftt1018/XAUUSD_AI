"""Cron job: refresh data -> signal -> telegram (used by Streamlit Cloud schedule / local task)."""
import argparse
from src.bootstrap import ensure_ready
from src.signal import get_signal
from src.telegram_send import send, format_signal

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="send even on WAIT (for testing)")
    args = ap.parse_args()
    ensure_ready()
    from src.data_fetch import update_all
    update_all()
    s = get_signal()
    print(s)
    if s["side"] != "WAIT" or args.force:
        send(format_signal(s))
    else:
        print("WAIT -> no push (avoids spam)")
