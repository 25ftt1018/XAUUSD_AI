"""Free Telegram sender. Set BOT_TOKEN + CHAT_ID in Streamlit secrets or env."""
import os
import requests


def _creds():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        try:
            import streamlit as st
            token = token or str(st.secrets.get("TELEGRAM_BOT_TOKEN", ""))
            chat = chat or str(st.secrets.get("TELEGRAM_CHAT_ID", ""))
        except Exception:
            pass
    return token, chat


def send(text: str) -> bool:
    token, chat = _creds()
    if not token or not chat:
        print("Telegram not configured. Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID.")
        print(text)
        return False
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text, "parse_mode": "Markdown"}, timeout=15)
    print(r.status_code, r.text[:200])
    return r.ok


def format_signal(s: dict) -> str:
    if s["side"] == "WAIT":
        return f"⏸ XAUUSD WAIT @ {s['price']} ({s['confidence']}%)\n{s['time']}"
    icon = "🟢" if s["side"] == "BUY" else "🔴"
    return (f"{icon} XAUUSD {s['side']} @ {s['price']}\n"
            f"Confidence: {s['confidence']}%\nSL: {s['sl']} | TP1: {s['tp1']} | TP2: {s['tp2']}\n{s['time']}")
