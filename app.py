"""Mobile-first Streamlit UI (free hosting). Add to Home Screen on iPhone."""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="XAUUSD AI", page_icon="🪙", layout="centered")

st.markdown("<h2 style='text-align:center'>🪙 XAUUSD AI Signals</h2>", unsafe_allow_html=True)
st.caption("Free Plan A • H1/M15 • Educational only, not financial advice.")

BASE = Path(__file__).parent
h1_path = BASE / "data" / "xau_h1.csv"

# --- Adjustable live chart ---
st.subheader("Live chart")
with st.expander("⚙️ Chart settings", expanded=False):
    tv_h = st.slider("Chart height", 400, 900, 620, 20)
    tv_int = st.selectbox("Timeframe", ["15", "60", "240", "D"], index=1)
    tv_theme = st.selectbox("Theme", ["dark", "light"], index=0)
st.components.v1.html(
    f'<div style="height:{tv_h}px"><div id="tv" style="height:100%"></div>'
    '<script src="https://s3.tradingview.com/tv.js"></script>'
    f'<script>new TradingView.widget({{symbol:"OANDA:XAUUSD",interval:"{tv_int}",theme:"{tv_theme}",'
    'style:"1",locale:"en",hide_side_toolbar:false,allow_symbol_change:true,'
    f'container_id:"tv",height:{tv_h},width:"100%"}});</script></div>',
    height=tv_h + 10)

# --- Latest signal ---
st.subheader("Latest signal")
try:
    from src.bootstrap import ensure_ready
    with st.spinner("Loading model (first run trains 1-2 min)..."):
        ensure_ready()
    from src.signal import get_signal
    s = get_signal()
    color = "green" if s["side"] == "BUY" else "red" if s["side"] == "SELL" else "gray"
    st.markdown(f":{color}[**{s['side']} @ {s['price']} ({s['confidence']}%)**]")
    st.write(f"SL: {s['sl']} | TP1: {s['tp1']} | TP2: {s['tp2']}")
    st.caption(f"{s['time']} • {s.get('reason','')}")
except Exception as e:
    st.warning(f"Model not trained yet. ({e})")

# --- History chart (non-squeezed) ---
if h1_path.exists():
    st.subheader("Price history")
    n = st.slider("Candles", 50, 300, 120, 10)
    h = st.slider("History height", 200, 500, 300, 20)
    df = pd.read_csv(h1_path, index_col=0, parse_dates=True).tail(n)
    df2 = df.reset_index().rename(columns={df.index.name or "index": "time"})
    time_col = df2.columns[0]
    import altair as alt
    chart = (
        alt.Chart(df2).mark_line(point=False).encode(
            x=alt.X(f"{time_col}:T", title=""),
            y=alt.Y("close:Q", title="XAUUSD", scale=alt.Scale(zero=False)),
            tooltip=[f"{time_col}:T", "close:Q"],
        ).properties(height=h).interactive()
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No local data yet on this device.")

st.divider()
st.caption("Telegram bot sends push alerts. Website = detail view.")
