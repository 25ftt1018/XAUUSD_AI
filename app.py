"""Mobile-first Streamlit UI (free hosting). Add to Home Screen on iPhone."""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="XAUUSD AI", page_icon="🪙", layout="centered")

st.markdown("<h2 style='text-align:center'>🪙 XAUUSD AI Signals</h2>", unsafe_allow_html=True)
st.caption("Free Plan A • H1/M15 • Educational only, not financial advice.")

BASE = Path(__file__).parent
h1_path = BASE / "data" / "xau_h1.csv"

# Live price chart (TradingView free widget, works on iPhone)
st.subheader("Live chart")
st.components.v1.html(
    '<div class="tradingview-widget-container"><div id="tv"></div>'
    '<script src="https://s3.tradingview.com/tv.js"></script>'
    '<script>new TradingView.widget({autosize:true,symbol:"OANDA:XAUUSD",interval:"60",theme:"dark",container_id:"tv"});</script>'
    '<div style="height:420px"></div></div>', height=440)

# Latest signal
st.subheader("Latest signal")
try:
    from src.bootstrap import ensure_ready
    with st.spinner("First run: downloading data + training (1-2 min)..."):
        ensure_ready()
    from src.signal import get_signal
    s = get_signal()
    color = "green" if s["side"] == "BUY" else "red" if s["side"] == "SELL" else "gray"
    st.markdown(f":{color}[**{s['side']} @ {s['price']} ({s['confidence']}%)**]")
    st.write(f"SL: {s['sl']} | TP1: {s['tp1']} | TP2: {s['tp2']}")
    st.caption(s["time"])
except Exception as e:
    st.warning(f"Model not trained yet. Run: `python -m src.data_fetch` then `python -m src.train`. ({e})")

# Recent candles
if h1_path.exists():
    df = pd.read_csv(h1_path, index_col=0, parse_dates=True).tail(100)
    st.subheader("Price (last 100 H1)")
    st.line_chart(df["close"])

st.divider()
st.caption("Telegram bot sends push alerts. Website = detail view.")
