"""Free Telegram sender. Set BOT_TOKEN + CHAT_ID in Streamlit secrets or env."""
import os
import requests


def _creds():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip().strip('"').strip("'")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip().strip('"').strip("'")
    if not token or not chat:
        try:
            import streamlit as st
            token = token or str(st.secrets.get("TELEGRAM_BOT_TOKEN", "")).strip()
            chat = chat or str(st.secrets.get("TELEGRAM_CHAT_ID", "")).strip()
        except Exception:
            pass
    return token.strip(), chat.strip()


def send(text: str) -> bool:
    token, chat = _creds()
    if not token or not chat:
        print("Telegram not configured. Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID.")
        print(text)
        return False
    if len(token) not in (45, 46, 47):
        print(f"Warning: token length {len(token)} looks off (expect ~46). Trimmed hidden chars.")
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text}, timeout=15)
    print(r.status_code, r.text[:300])
    return r.ok


def format_signal(s: dict) -> str:
    if s["side"] == "WAIT":
        return f"⏸ XAUUSD WAIT @ {s['price']} ({s['confidence']}%)\n{s.get('reason','')}\n{s['time']}"
    icon = "🟢" if s["side"] == "BUY" else "🔴"
    reasons = "\n".join(f"• {r}" for r in s.get("reasons", []))
    return (f"{icon} XAUUSD {s['side']} @ {s['price']}\n"
            f"Confidence: {s['confidence']}%\nSL: {s['sl']} | TP1: {s['tp1']} | TP2: {s['tp2']} | TP3: {s.get('tp3')}\n"
            f"{reasons}\n{s['time']}")
