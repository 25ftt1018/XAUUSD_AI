"""Mobile-first Streamlit UI — signal-card style (inspired by 3rd-eye screenshot)."""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="XAUUSD AI", page_icon="🪙", layout="centered")

CSS = """
<style>
body { background:#070b16; }
.card { background:linear-gradient(180deg,#0d1426,#0a0f1f); border:1px solid #1de9b6aa;
  border-radius:18px; padding:16px; box-shadow:0 0 24px #1de9b633; }
.pill { display:inline-block; padding:3px 12px; border-radius:999px; font-size:12px; font-weight:700; }
.pill-ai { background:#7c5cff33; color:#b9a7ff; border:1px solid #7c5cff88; }
.pill-live { background:#0a2e22; color:#1de9b6; border:1px solid #1de9b655; }
.side-buy { background:#0d3b2e; color:#1de9b6; border:2px solid #1de9b6; border-radius:10px;
  padding:6px 18px; font-weight:800; }
.side-sell { background:#3b0d0d; color:#ff6b6b; border:2px solid #ff6b6b; border-radius:10px;
  padding:6px 18px; font-weight:800; }
.side-wait { background:#222; color:#aaa; border:2px solid #555; border-radius:10px;
  padding:6px 18px; font-weight:800; }
.status { background:#0e2a22; border:1px solid #1de9b655; color:#1de9b6; border-radius:10px;
  padding:8px 12px; font-weight:700; text-align:center; margin:10px 0; }
.status.wait { background:#1a1a1a; color:#999; border-color:#444; }
.reasonbox { background:#141b3d; border-left:4px solid #7c5cff; border-radius:8px;
  padding:10px 12px; font-size:13px; color:#dfe3ff; margin:8px 0; }
.entry { background:#0a2540; border:1px solid #2f81f7aa; border-radius:12px; text-align:center;
  padding:10px; margin:8px 0; }
.entry .lbl { font-size:11px; letter-spacing:2px; color:#9fb3d9; }
.entry .val { font-size:34px; font-weight:800; color:#fff; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:8px 0; }
.cell { border-radius:10px; padding:8px; text-align:center; }
.cell .lbl { font-size:10px; letter-spacing:1px; opacity:.8; }
.cell .val { font-size:17px; font-weight:800; }
.cell.sl { background:#2a1440; border:1px solid #7c5cff88; color:#d9c8ff; }
.cell.tp { background:#0d2b26; border:1px solid #1de9b666; color:#b8ffe9; }
.screener { background:#0a0f1f; border:1px solid #ffffff22; border-radius:10px;
  padding:8px 12px; font-size:12px; color:#cbd5e1; }
.sent { font-size:11px; color:#888; margin-top:8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center'>🪙 XAUUSD AI Signals</h2>", unsafe_allow_html=True)
st.caption("Free Plan A • H1/M15 • Educational only, not financial advice.")

# --- News banner + always-visible upcoming list ---
try:
    from src.news import status as _news_status, load_events as _load_events
    _ns = _news_status()
    if _ns.get("blocked"):
        st.warning(f"⚠️ {_ns['title']} ({_ns['mins_to']:+.0f} min) — new signals paused")
    elif _ns.get("next"):
        from datetime import datetime, timezone
        _t = datetime.fromisoformat(_ns["next"]["time_utc"])
        _mins = (_t - datetime.now(timezone.utc)).total_seconds() / 60
        if _mins < 240:
            st.info(f"📰 Next: {_ns['next']['title']} in {_mins:.0f} min (fcst {_ns['next'].get('forecast','—')})")
    with st.expander("📰 Upcoming high-impact USD news", expanded=False):
        from datetime import datetime, timezone, timedelta
        _now = datetime.now(timezone.utc)
        _rows = []
        for _e in _load_events():
            _t = datetime.fromisoformat(_e["time_utc"])
            if _t > _now - timedelta(minutes=30):
                _mins = (_t - _now).total_seconds() / 60
                _when = f"in {_mins:.0f}m" if _mins >= 0 else f"{- _mins:.0f}m ago"
                _rows.append((_t, f"{'⭐' if _e.get('key') else '•'} {_e['title']} — {_t:%a %H:%M} UTC ({_when})"))
            if len(_rows) >= 5:
                break
        if _rows:
            for _, _line in sorted(_rows):
                st.write(_line)
        else:
            st.write("No upcoming events cached.")
except Exception:
    pass

BASE = Path(__file__).parent
h1_path = BASE / "data" / "xau_h1.csv"

# --- Signal card ---
tf = st.radio("Model", ["H1 intraday", "H4 swing ⭐"], index=1, horizontal=True)
try:
    from src.bootstrap import ensure_ready
    with st.spinner("Loading model (first run trains 1-2 min)..."):
        ensure_ready()
    if tf.startswith("H4"):
        from src.signal_h4 import get_signal_h4 as _get
    else:
        from src.signal import get_signal as _get
    s = _get()
    side = s["side"]
    side_cls = "side-buy" if side == "BUY" else "side-sell" if side == "SELL" else "side-wait"
    screener = s.get("screener", {})
    scr_html = " • ".join(f"{k}: <b>{v}</b>" for k, v in screener.items())
    reasons_html = "".join(f"<div>• {r}</div>" for r in s.get("reasons", []))

    if side == "WAIT":
        status_html = f'<div class="status wait">WAIT — {s.get("reason","")} • {s["confidence"]}%</div>'
    else:
        status_html = (f'<div class="status">RUNNING {s["running_pips"]:+.0f} pip '
                       f'<span style="float:right">peak +{s["peak_pips"]:.0f}</span></div>')

    st.markdown(f"""
<div class="card">
  <div>🔥 <b>XAUUSD</b> <span style="font-size:11px;color:#888">MT5 BROKER FEED</span></div>
  <div style="margin:6px 0"><span class="pill pill-ai">3RD EYES • AI</span>
    <span class="pill pill-live" style="float:right">● Signal Running</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin:8px 0">
    <div><b style="font-size:22px">XAUUSD</b>
      <span class="pill pill-ai">Analysis {s["confidence"]}%</span></div>
    <div class="{side_cls}">{'↗' if side=='BUY' else '↘' if side=='SELL' else '⏸'} {side}</div>
  </div>
  {status_html}
  <div style="font-size:11px;color:#8b93b8;letter-spacing:1px">SIGNAL REASON</div>
  <div class="reasonbox">{reasons_html}</div>
  <div class="entry"><div class="lbl">ENTRY</div><div class="val">{s["price"]:,.2f}</div></div>
  <div class="grid">
    <div class="cell sl"><div class="lbl">STOP LOSS (SL)</div><div class="val">{s["sl"] or "—"}</div></div>
    <div class="cell tp"><div class="lbl">TP 1 ✓</div><div class="val">{s["tp1"] or "—"}</div></div>
    <div class="cell tp"><div class="lbl">TP 2</div><div class="val">{s["tp2"] or "—"}</div></div>
    <div class="cell tp"><div class="lbl">TP 3</div><div class="val">{s.get("tp3") or "—"}</div></div>
  </div>
  <div class="screener">🪙 XAUUSD SCREENER<br>{scr_html}</div>
  <div class="sent">● SENT: {s["time"]}</div>
</div>""", unsafe_allow_html=True)
except Exception as e:
    st.warning(f"Signal unavailable. ({e})")

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

# --- History chart (non-squeezed) ---
if h1_path.exists():
    st.subheader("Price history")
    n = st.slider("Candles", 50, 300, 120, 10)
    h = st.slider("History height", 200, 500, 300, 20)
    df = pd.read_csv(h1_path, index_col=0, parse_dates=True).tail(n)
    df2 = df.reset_index()
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

st.divider()
st.caption("Telegram bot sends push alerts. Website = detail view.")
