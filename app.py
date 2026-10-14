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
.card.buy { border-color:#1de9b6; box-shadow:0 0 32px #1de9b655; }
.card.sell { border-color:#ff6b6b; box-shadow:0 0 32px #ff6b6b55; }
.card.wait { border-color:#444; box-shadow:none; }
.pill { display:inline-block; padding:3px 12px; border-radius:999px; font-size:12px; font-weight:700; }
.pill-ai { background:#7c5cff33; color:#b9a7ff; border:1px solid #7c5cff88; }
.pill-live { background:#0a2e22; color:#1de9b6; border:1px solid #1de9b655; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.55; } }
.pulse { animation:pulse 1.6s infinite; }
.side-buy { background:#00e676; color:#04140c; border:2px solid #00e676; border-radius:10px;
  padding:8px 22px; font-weight:900; font-size:17px; }
.side-sell { background:#ff5252; color:#1c0404; border:2px solid #ff5252; border-radius:10px;
  padding:8px 22px; font-weight:900; font-size:17px; }
.side-wait { background:#1c1c1c; color:#777; border:2px dashed #555; border-radius:10px;
  padding:8px 22px; font-weight:800; font-size:15px; }
.status { background:#0e2a22; border:1px solid #1de9b655; color:#1de9b6; border-radius:10px;
  padding:8px 12px; font-weight:700; text-align:center; margin:10px 0; }
.status.wait { background:#141414; color:#888; border-style:dashed; border-color:#444; }
.reasonbox { background:#141b3d; border-left:4px solid #7c5cff; border-radius:8px;
  padding:10px 12px; font-size:13px; color:#dfe3ff; margin:8px 0; }
.entry { background:#0a2540; border:1px solid #2f81f7aa; border-radius:12px; text-align:center;
  padding:12px; margin:8px 0; }
.entry .lbl { font-size:11px; letter-spacing:2px; color:#9fb3d9; }
.entry .val { font-size:44px; font-weight:900; color:#fff; line-height:1.1; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:8px 0; }
.cell { border-radius:10px; padding:10px 8px; text-align:center; }
.cell .lbl { font-size:10px; letter-spacing:1px; opacity:.85; }
.cell .val { font-size:19px; font-weight:800; }
.cell .r { font-size:10px; opacity:.7; }
.cell.sl { background:#2a1440; border:1px solid #7c5cff88; color:#d9c8ff; }
.cell.tp { background:#0d2b26; border:1px solid #1de9b666; color:#b8ffe9; }
.cell.off { background:#151515; border:1px dashed #444; color:#666; }
.screener { background:#0a0f1f; border:1px solid #ffffff22; border-radius:10px;
  padding:8px 12px; font-size:12px; color:#cbd5e1; }
.sent { font-size:11px; color:#888; margin-top:8px; }
.newstable { width:100%; border-collapse:collapse; font-size:13px; }
.newstable td, .newstable th { padding:7px 6px; border-bottom:1px solid #ffffff14; text-align:left; }
.newstable tr.key td { background:#ffd54d11; }
.bull { background:#00e67622; color:#00e676; border:1px solid #00e67688; border-radius:6px;
  padding:1px 8px; font-weight:800; white-space:nowrap; }
.bear { background:#ff525222; color:#ff8a80; border:1px solid #ff525288; border-radius:6px;
  padding:1px 8px; font-weight:800; white-space:nowrap; }
.neu { background:#ffffff11; color:#aaa; border:1px solid #555; border-radius:6px;
  padding:1px 8px; font-weight:800; white-space:nowrap; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center'>🪙 XAUUSD AI Signals</h2>", unsafe_allow_html=True)
st.caption("Free Plan A • H1/M15 • Educational only, not financial advice.")

with st.expander("⚙️ Display", expanded=False):
    _auto = st.toggle("Auto-refresh live P/L (30s)", value=True)

# --- News banner + always-visible upcoming list ---
try:
    if _auto:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=30 * 1000, key="pl30")
        except Exception:
            pass
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
        def _dur(m: float) -> str:
            if m < 0:
                m = -m
                suf = "ago"
                pre = ""
            else:
                suf = ""
                pre = "in "
            if m < 60:
                return f"{pre}{m:.0f}m {suf}".strip()
            if m < 1440:
                return f"{pre}{int(m // 60)}h {int(m % 60):02d}m {suf}".strip()
            return f"{pre}{int(m // 1440)}d {int((m % 1440) // 60)}h {suf}".strip()
        _c1, _c2 = st.columns([3, 1])
        with _c2:
            if st.button("↻ Refresh", key="newsref"):
                try:
                    from src.news import update_calendar as _upd
                    _upd()
                    st.rerun()
                except Exception as _e:
                    st.warning(f"Refresh failed: {_e}")
        try:
            from src.news_bias import current_bias as _bias
            _b = _bias()
            _act = _b.get("action", "WAIT")
            _pill = "bull" if _act == "BUY" else "bear" if _act == "SELL" else "neu"
            _b_txt = f"{_b['label']} [{_act}]"
        except Exception:
            _b, _b_txt, _pill = {"why": []}, "n/a", "neu"
        st.caption(f"Positioning bias, not a prediction: **{_b_txt}** — {', '.join(_b.get('why', []))}")
        _now = datetime.now(timezone.utc)
        _rows, _past = [], []
        for _e in _load_events():
            _t = datetime.fromisoformat(_e["time_utc"])
            _mins = (_t - _now).total_seconds() / 60
            if _mins >= -30:
                _rows.append((_t, _e, _dur(_mins)))
            elif _mins >= -24 * 60:
                _past.append((_t, _e, _dur(_mins)))
            if len(_rows) >= 5 and len(_past) >= 3:
                break
        if _rows:
            _why = "".join(f"<div>• {w}</div>" for w in _b.get("why", []))
            for _t, _e, _when in sorted(_rows):
                _star = "⭐ " if _e.get("key") else ""
                st.markdown(f"""
<div class="card" style="margin:8px 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div><b>{_star}{_e['title']}</b></div>
    <div><span class="{_pill}">{_b_txt}</span></div>
  </div>
  <div style="font-size:12px;color:#9fb3d9;margin:6px 0">🕐 {_t:%A %H:%M} UTC ({_when})</div>
  <div class="reasonbox">fcst <b>{_e.get('forecast') or '—'}</b> • prev <b>{_e.get('previous') or '—'}</b><br>{_why}</div>
  <div class="sent">Signals pause ±30 min around release • bias is positioning, not a prediction</div>
</div>""", unsafe_allow_html=True)
            for _t, _e, _when in sorted(_past)[-3:]:
                st.caption(f"{_e['title']} ✅ {_t:%a %H:%M} ({_when})")
        else:
            if _past:
                st.markdown(
                    "No upcoming events — week done. Recent: " +
                    ", ".join(f"{_e['title']} ✅ ({_w})" for _, _e, _w in sorted(_past)[-3:]))
            else:
                st.write("No events cached. Tap ↻ Refresh (Sunday rotation / network).")
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
    card_cls = "buy" if side == "BUY" else "sell" if side == "SELL" else "wait"
    side_cls = "side-buy" if side == "BUY" else "side-sell" if side == "SELL" else "side-wait"
    side_txt = ("↗ BUY" if side == "BUY" else "↘ SELL" if side == "SELL" else "⏸ NO TRADE")
    screener = s.get("screener", {})
    scr_html = " • ".join(f"{k}: <b>{v}</b>" for k, v in screener.items())
    reasons_html = "".join(f"<div>• {r}</div>" for r in s.get("reasons", []))

    # Live spot vs signal entry (paper signal, NOT your broker position)
    try:
        from src.data_fetch import live_spot
        _spot = live_spot() or s["price"]
        _d = 1 if side == "BUY" else -1 if side == "SELL" else 0
        _run = (_spot - s["price"]) / 0.1 * _d
    except Exception:
        _spot, _run = s["price"], s.get("running_pips", 0) or 0

    if side == "WAIT":
        status_html = f'<div class="status wait">NO TRADE — {s.get("reason","")} • {s["confidence"]}%</div>'
        live_txt = ""
    else:
        _sl, _tp1 = s.get("sl"), s.get("tp1")
        if side == "BUY":
            _hit_sl = _sl is not None and _spot <= _sl
            _hit_tp1 = _tp1 is not None and _spot >= _tp1
        else:
            _hit_sl = _sl is not None and _spot >= _sl
            _hit_tp1 = _tp1 is not None and _spot <= _tp1
        _to_tp1 = abs((_tp1 - _spot) / 0.1) if _tp1 else None
        _to_sl = abs((_spot - _sl) / 0.1) if _sl else None
        _sub = (f"{_to_tp1:.0f} pip to TP1 • {_to_sl:.0f} pip to SL" if _to_tp1 is not None else "")
        if _hit_sl:
            status_html = (f'<div class="status wait">❌ STOPPED OUT {_run:+.0f} pip '
                           f'<br><span style="font-size:11px">paper signal hit SL — wait for next signal</span></div>')
        elif _hit_tp1:
            status_html = (f'<div class="status pulse">✅ TP1 HIT — BREAK EVEN SET ({_run:+.0f} pip)'
                           f'<br><span style="font-size:11px">{_sub}</span></div>')
        else:
            status_html = (f'<div class="status">SIGNAL P/L {_run:+.0f} pip (paper, not your position)'
                           f'<br><span style="font-size:11px">{_sub}</span></div>')
        live_txt = f'<span class="pill pill-live">paper {_run:+.0f} pip</span>'

    _cell = lambda lbl, val, cls, r="": (
        f'<div class="cell {cls}"><div class="lbl">{lbl}</div><div class="val">{val or "—"}</div>'
        f'<div class="r">{r}</div></div>')
    _off = "off" if side == "WAIT" else ""

    st.markdown(f"""
<div class="card {card_cls}">
  <div>🔥 <b>XAUUSD</b> <span style="font-size:11px;color:#888">MT5 BROKER FEED</span></div>
  <div style="margin:6px 0"><span class="pill pill-ai">3RD EYES • AI</span>
    <span class="pill pill-live pulse" style="float:right">● Signal Running</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin:8px 0">
    <div><b style="font-size:22px">XAUUSD</b>
      <span class="pill pill-ai">Analysis {s["confidence"]}%</span> {live_txt}</div>
    <div class="{side_cls}">{side_txt}</div>
  </div>
  {status_html}
  <div style="font-size:11px;color:#8b93b8;letter-spacing:1px">SIGNAL REASON</div>
  <div class="reasonbox">{reasons_html}</div>
  <div class="entry"><div class="lbl">ENTRY</div><div class="val">{s["price"]:,.2f}</div></div>
  <div class="grid">
    {_cell("STOP LOSS (SL)", f'{s["sl"]:,.2f}' if s["sl"] else None, "sl " + _off)}
    {_cell("TP 1 ✓", f'{s["tp1"]:,.2f}' if s["tp1"] else None, "tp " + _off, "+1R")}
    {_cell("TP 2", f'{s["tp2"]:,.2f}' if s["tp2"] else None, "tp " + _off, "+2R")}
    {_cell("TP 3", f'{s.get("tp3"):,.2f}' if s.get("tp3") else None, "tp " + _off, "+3R")}
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
