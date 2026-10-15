"""Free Telegram sender. Set BOT_TOKEN + CHAT_ID in Streamlit secrets or env."""
import os
import requests


def _creds():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip().strip('"').strip("'")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip().strip('"').strip("'")
    if not token or not chat:
        # Read Streamlit secrets file directly: importing streamlit from a
        # plain `python check_signal.py` run prints the "streamlit run" warning.
        try:
            from pathlib import Path
            txt = (Path(__file__).parent.parent / ".streamlit" / "secrets.toml").read_text()
            import re
            if not token:
                m = re.search(r'TELEGRAM_BOT_TOKEN\s*=\s*["\']([^"\']+)["\']', txt)
                if m:
                    token = m.group(1).strip()
            if not chat:
                m = re.search(r'TELEGRAM_CHAT_ID\s*=\s*["\']([^"\']+)["\']', txt)
                if m:
                    chat = m.group(1).strip()
        except Exception:
            pass
    return token.strip(), chat.strip()


def _safe_print(*a):
    try:
        print(*a)
    except UnicodeEncodeError:
        print(*[str(x).encode("ascii", "replace").decode() for x in a])


def send(text: str) -> bool:
    token, chat = _creds()
    if not token or not chat:
        _safe_print("Telegram not configured. Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID.")
        _safe_print(text)
        return False
    if len(token) not in (45, 46, 47):
        print(f"Warning: token length {len(token)} looks off (expect ~46). Trimmed hidden chars.")
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text}, timeout=15)
    try:
        print(r.status_code, r.text[:300])
    except UnicodeEncodeError:
        _safe_print(r.status_code, r.text[:300])
    return r.ok


def format_signal(s: dict) -> str:
    if s["side"] == "WAIT":
        return f"⏸ XAUUSD WAIT @ {s['price']} ({s['confidence']}%)\n{s.get('reason','')}\n{s['time']}"
    icon = "🟢" if s["side"] == "BUY" else "🔴"
    reasons = "\n".join(f"• {r}" for r in s.get("reasons", []))
    spot = s.get("spot")
    spot_line = f"\nSpot: {spot:.2f} (entry GC=F futures {s['price']})" if spot else "\nEntry: GC=F futures (spot n/a)"
    return (f"{icon} XAUUSD {s['side']} @ {s['price']}{spot_line}\n"
            f"Model: {s['confidence']}% (hist ~{s.get('hist_conf', 50)}%)\nSL: {s['sl']} | TP1: {s['tp1']} | TP2: {s['tp2']} | TP3: {s.get('tp3')}\n"
            f"{reasons}\n{s['time']}")
