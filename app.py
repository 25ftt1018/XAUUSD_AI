"""Streamlit UI — responsive signal cards (phone + desktop)."""
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="XAUUSD AI", page_icon="🪙", layout="wide")

CSS = """
<style>
:root { --bg:#070b16; --card:#0d1426; --up:#1de9b6; --down:#ff6b6b; }
body { background:var(--bg); }
.block-container { max-width:1100px; margin:0 auto; padding:1rem 16px 3rem; }
.card { background:linear-gradient(180deg,#0d1426,#0a0f1f); border:1px solid #1de9b6aa;
  border-radius:18px; padding:16px; box-shadow:0 0 24px #1de9b633; max-width:640px; margin:0 auto; }
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
.entry .val { font-size:clamp(32px,8vw,44px); font-weight:900; color:#fff; line-height:1.1; }
.entry .spot { font-size:12px; color:#9fb3d9; margin-top:4px; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:8px 0; }
@media (min-width:900px) { .grid { grid-template-columns:repeat(4,1fr); } .card { max-width:760px; } }
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
.quote { display:flex; gap:8px; align-items:stretch; max-width:640px; margin:0 auto 10px; }
.qbox { flex:1; border-radius:10px; padding:8px 6px; text-align:center; font-weight:900; }
.qbox .v { font-size:clamp(17px,4.5vw,22px); font-variant-numeric:tabular-nums; }
.qbox .t { font-size:11px; letter-spacing:2px; opacity:.85; }
.q-bid { background:#2a0d0d; border:1px solid #ff5252aa; color:#ff8a80; }
.q-ask { background:#0a1c3f; border:1px solid #2f81f7aa; color:#7fb3ff; }
.q-mid { flex:0 0 64px; align-self:center; text-align:center; color:#888; font-size:12px; font-weight:800; }
@media (min-width:900px) { .quote { max-width:760px; } }
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
        _TZ_OPTS = ["Asia/Manila", "Asia/Singapore", "UTC", "Africa/Lagos", "Europe/London", "America/New_York", "Europe/Berlin", "Asia/Dubai"]
        _tz_name = st.selectbox("Show times in", _TZ_OPTS, index=0, key="tzpick")
        def _local_str(iso_utc: str) -> str:
            try:
                from zoneinfo import ZoneInfo
                _t = datetime.fromisoformat(iso_utc)
                _l = _t.astimezone(ZoneInfo(_tz_name))
                return _l.strftime("%A %H:%M") + f" ({_tz_name.split('/')[-1].replace('_', ' ')})"
            except Exception:
                return ""
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
        _evs, _err = [], None
        try:
            _evs = _load_events()
        except Exception as _e:
            _err = str(_e)
        from src.news import last_source as _src
        try:
            _src_txt = _src()
        except Exception:
            _src_txt = "?"
        st.caption(f"Source: {_src_txt}")
        if _err:
            st.warning(f"News load error: {_err}")
        _rows, _past = [], []
        for _e in _evs:
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
            for _t, _e, _when in sorted(_rows, key=lambda r: r[0]):
                _star = "⭐ " if _e.get("key") else ""
                _loc = _local_str(_e["time_utc"])
                _loc_html = f'<div style="font-size:12px;color:#1de9b6;margin:0 0 6px">📍 {_loc}</div>' if _loc else ""
                st.markdown(f"""
<div class="card" style="margin:8px 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div><b>{_star}{_e['title']}</b></div>
    <div><span class="{_pill}">{_b_txt}</span></div>
  </div>
  <div style="font-size:12px;color:#9fb3d9;margin:6px 0">🕐 {_t:%A %H:%M} UTC ({_when})</div>
  {_loc_html}
  <div class="reasonbox">fcst <b>{_e.get('forecast') or '—'}</b> • prev <b>{_e.get('previous') or '—'}</b><br>{_why}</div>
  <div class="sent">Signals pause ±30 min around release • bias is positioning, not a prediction</div>
</div>""", unsafe_allow_html=True)
            for _t, _e, _when in sorted(_past, key=lambda r: r[0])[-3:]:
                st.caption(f"{_e['title']} ✅ {_t:%a %H:%M} ({_when})")
        else:
            if _past:
                st.markdown(
                    "No upcoming events — week done. Recent: " +
                    ", ".join(f"{_e['title']} ✅ ({_w})" for _, _e, _w in sorted(_past, key=lambda r: r[0])[-3:]))
            else:
                st.write("No events cached. Tap ↻ Refresh (Sunday rotation / network).")
        try:
            from src.news import scheduled_future as _sched
            _fut = [e for e in _sched()]
            if _fut:
                st.caption("Scheduled ahead (provisional dates, no blackout until confirmed):")
                for _e in _fut[:4]:
                    _t = datetime.fromisoformat(_e["time_utc"])
                    st.write(f"📅 {_e['title']} — {_t:%a %b %d %H:%M} UTC")
        except Exception:
            pass
except Exception as _outer_e:
    st.warning(f"News section error: {_outer_e}")

BASE = Path(__file__).parent

# --- Live quote bar (MT5-style bid/ask, indicative) ---
QUOTE_SPREAD_USD = 0.51  # typical gold spread; gold-api gives mid only
try:
    from src.data_fetch import live_spot as _quote_spot_fn
    from datetime import datetime, timezone as _tz
    _mid = _quote_spot_fn()
    if _mid:
        from datetime import datetime as _dt
        _now_utc = _dt.now(_tz.utc)
        _half = QUOTE_SPREAD_USD / 2
        _bid, _ask = _mid - _half, _mid + _half
        _prev = st.session_state.get("_last_mid")
        st.session_state["_last_mid"] = _mid
        _arrow = "▲" if _prev and _mid > _prev else "▼" if _prev and _mid < _prev else "●"
        _pts = QUOTE_SPREAD_USD / 0.01
        st.markdown(f"""
<div class="quote">
  <div class="qbox q-bid"><div class="v">{_bid:,.3f}</div><div class="t">SELL</div></div>
  <div class="q-mid">{_arrow}<br>{_pts:.1f}</div>
  <div class="qbox q-ask"><div class="v">{_ask:,.3f}</div><div class="t">BUY</div></div>
</div>
<div style="text-align:center;font-size:11px;color:#888;max-width:640px;margin:-4px auto 10px">LIVE indicative — follows chart • as of {_now_utc:%H:%M:%S} UTC<br>mid {_mid:,.2f} via gold-api, spread ${QUOTE_SPREAD_USD:.2f} • not your broker quote</div>""", unsafe_allow_html=True)
    else:
        st.caption("Live quote unavailable (gold-api offline) — showing signal entry only.")
except Exception:
    pass

# --- Signal card (always on top) ---
tf = st.radio("Model", ["H1 intraday", "H4 swing ⭐", "M30 scalp"], index=1, horizontal=True)
try:
    from src.bootstrap import ensure_ready
    with st.spinner("Loading model (first run trains 1-2 min)..."):
        ensure_ready()
    if tf.startswith("H4"):
        from src.signal_h4 import get_signal_h4 as _get
    elif tf.startswith("M30"):
        from src.signal_m30 import get_signal_m30 as _get
    else:
        from src.signal import get_signal as _get
    s = _get()
    from datetime import datetime, timezone
    _loaded = datetime.now(timezone.utc)
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
    _spot_line = f"Spot {_spot:,.2f} • GC=F futures entry" if _spot else "GC=F futures entry (spot n/a)"

    st.markdown(f"""
<div class="card {card_cls}">
  <div>🔥 <b>XAUUSD</b> <span style="font-size:11px;color:#888">MT5 BROKER FEED</span></div>
  <div style="margin:6px 0"><span class="pill pill-ai">3RD EYES • AI</span>
    <span class="pill pill-live pulse" style="float:right">● Signal Running</span></div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin:8px 0">
    <div><b style="font-size:22px">XAUUSD</b>
      <span class="pill pill-ai">Analysis {s["confidence"]}% · hist ~{s.get("hist_conf", 50)}%</span> {live_txt}</div>
    <div class="{side_cls}">{side_txt}</div>
  </div>
  {status_html}
  <div style="font-size:11px;color:#8b93b8;letter-spacing:1px">SIGNAL REASON</div>
  <div class="reasonbox">{reasons_html}</div>
  <div class="entry"><div class="lbl">ENTRY</div><div class="val">{s["price"]:,.2f}</div><div class="spot">{_spot_line}</div></div>
  <div class="grid">
    {_cell("STOP LOSS (SL)", f'{s["sl"]:,.2f}' if s["sl"] else None, "sl " + _off)}
    {_cell("TP 1 ✓", f'{s["tp1"]:,.2f}' if s["tp1"] else None, "tp " + _off, "+1R")}
    {_cell("TP 2", f'{s["tp2"]:,.2f}' if s["tp2"] else None, "tp " + _off, "+2R")}
    {_cell("TP 3", f'{s.get("tp3"):,.2f}' if s.get("tp3") else None, "tp " + _off, "+3R")}
  </div>
  <div class="screener">🪙 XAUUSD SCREENER<br>{scr_html}</div>
  <div class="sent">● SIGNAL CANDLE: {s["time"]} • CARD LOADED: {_loaded:%H:%M:%S} UTC<br>P/L ticks live (30s) • signal changes on new candle/retrain only</div>
</div>""", unsafe_allow_html=True)
except Exception as e:
    st.warning(f"Signal unavailable. ({e})")

tab_chart, tab_board = st.tabs(["📈 Chart", "📒 Scoreboard"])
with tab_chart:
    # --- Live chart only (price-history line chart removed) ---
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

with tab_board:
    _tf_filter = st.selectbox("Filter", ["All", "H1", "H4 SWING", "OPEN", "TP1", "SL"], index=0)
    try:
        from src.scoreboard import mark_outcomes, summary
        _log = mark_outcomes()
        if _log is not None and not _log.empty:
            if _tf_filter in ("H1", "H4 SWING"):
                _log = _log[_log["tf"] == _tf_filter]
            elif _tf_filter in ("OPEN", "TP1", "SL"):
                _log = _log[_log["outcome"] == _tf_filter]
            _sum = summary(_log)
            _c1, _c2, _c3, _c4 = st.columns(4)
            _c1.metric("Signals", _sum["total"])
            _c2.metric("TP1 / SL", f"{_sum['tp1']} / {_sum['sl']}")
            _c3.metric("Winrate", f"{_sum['winrate']}%")
            _c4.metric("Net pips", f"{_sum['net_pips']:+.0f}")
            st.dataframe(_log[["time", "tf", "side", "entry", "sl", "tp1",
                                "conf", "hist_conf", "outcome", "pips"]].tail(20),
                         use_container_width=True)
        else:
            st.caption("No paper signals logged yet - first BUY/SELL will appear here with auto-marked TP1/SL.")
    except Exception as _e:
        st.caption(f"Scoreboard unavailable: {_e}")
st.caption("Telegram bot sends push alerts. Website = detail view.")
