"""Pre-news bias: positioning (technicals) + expectation (forecast vs previous).

Displays expectation vs positioning separately. Action is WAIT on conflict
or weak votes — it does NOT predict the surprise (actual - forecast ~50/50).
Blackout in src/news.py still blocks real signals ±30 min.
"""
import re
from datetime import datetime, timezone

import pandas as pd
import joblib
from config import DATA_DIR, DATA_H1_PATH, MODELS_DIR

# Titles where a HIGHER print is dovish for USD (= bullish gold). Everything
# else hot = hawkish USD = bearish gold.
_INVERSE_TITLES = ("unemployment",)
_EPS = 1e-9


def _parse_num(s: str | None) -> float | None:
    if not s:
        return None
    m = re.search(r"[-+]?\d*\.?\d+", str(s).replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def expectation_for_event(title: str, forecast: str | None, previous: str | None) -> dict:
    """Per-release implication: hot = bearish gold (except Unemployment)."""
    fcst, prev = _parse_num(forecast), _parse_num(previous)
    if fcst is None or prev is None:
        return {"votes": 0, "text": "forecast n/a"}
    if abs(fcst - prev) < _EPS:
        return {"votes": 0, "text": f"in-line {forecast} vs {previous}"}
    inverse = any(k in (title or "").lower() for k in _INVERSE_TITLES)
    hot = (fcst - prev) > 0
    v = (-1 if hot else 1) * (-1 if inverse else 1)
    direction = "bearish gold (hot expected)" if v < 0 else "bullish gold (cold expected)"
    return {"votes": v, "text": f"{forecast} vs {previous} -> {direction}"}


def get_expectation(now: datetime | None = None, window_h: int = 72) -> dict:
    """Consensus expectation from forecast vs previous for the next event cluster.

    Groups all key events within 60 min of the next upcoming key event (PPI day
    has PPI + Core PPI + Retail Sales at the same 12:30 UTC). Hot = bearish gold.
    Returns {votes, why, events}.
    """
    now = now or datetime.now(timezone.utc)
    try:
        from src.news import load_events
        events = load_events()
    except Exception as e:
        return {"votes": 0, "why": [f"calendar n/a ({e})"], "events": []}
    upcoming = []
    for e in events:
        try:
            t = datetime.fromisoformat(e["time_utc"])
        except Exception:
            continue
        mins = (t - now).total_seconds() / 60
        if -30 <= mins <= window_h * 60 and e.get("key"):
            upcoming.append((t, e))
    if not upcoming:
        return {"votes": 0, "why": ["no upcoming key event"], "events": []}
    upcoming.sort(key=lambda r: r[0])
    t0 = upcoming[0][0]
    cluster = [e for t, e in upcoming if abs((t - t0).total_seconds()) <= 60 * 60]
    votes, why, details = 0, [], []
    for e in cluster:
        title = e.get("title", "?")
        fcst_s, prev_s = e.get("forecast") or "", e.get("previous") or ""
        r = expectation_for_event(title, fcst_s, prev_s)
        if r["votes"] == 0 and r["text"] == "forecast n/a":
            continue
        votes += r["votes"]
        details.append({"title": title, "votes": r["votes"], "text": r["text"]})
        why.append(f"{title} {r['text']}")
    votes = max(-2, min(2, votes))  # cap: don't overweight vs positioning
    if not why:
        why = ["forecasts n/a (no fcst/prev yet)"]
    return {"votes": votes, "why": why, "events": [e["title"] for e in cluster], "details": details}


def current_bias() -> dict:
    pos_votes, pos_why = 0, []
    # 1. H4 model
    try:
        from src.signal_h4 import get_signal_h4
        s = get_signal_h4()
        if s["side"] == "BUY":
            pos_votes += 2; pos_why.append("H4 BUY")
        elif s["side"] == "SELL":
            pos_votes -= 2; pos_why.append("H4 SELL")
        else:
            pos_why.append(f"H4 WAIT {s['confidence']}%")
    except Exception as e:
        pos_why.append(f"H4 n/a ({e})")
    # 2. 24h gold drift
    try:
        df = pd.read_csv(DATA_H1_PATH, index_col=0, parse_dates=True)
        drift = (df["close"].iloc[-1] - df["close"].iloc[-24]) / df["close"].iloc[-24] * 100
        if drift > 0.15:
            pos_votes += 1; pos_why.append(f"24h +{drift:.2f}%")
        elif drift < -0.15:
            pos_votes -= 1; pos_why.append(f"24h {drift:.2f}%")
        else:
            pos_why.append(f"24h flat {drift:+.2f}%")
        # 3. RSI/EMA
        from src.features import add_features
        f = add_features(df).iloc[-1]
        if f["rsi14"] > 55 and f["trend"] > 0:
            pos_votes += 1; pos_why.append(f"RSI {f['rsi14']:.0f} + above EMA50")
        elif f["rsi14"] < 45 and f["trend"] < 0:
            pos_votes -= 1; pos_why.append(f"RSI {f['rsi14']:.0f} + below EMA50")
    except Exception as e:
        pos_why.append(f"tech n/a ({e})")
    # 4. DXY (inverse: strong dollar = gold headwind)
    try:
        from src.data_fetch import load_dxy
        d = load_dxy()
        chg = (d["close"].iloc[-1] - d["close"].iloc[-24]) / d["close"].iloc[-24] * 100
        if chg > 0.1:
            pos_votes -= 1; pos_why.append(f"DXY +{chg:.2f}% headwind")
        elif chg < -0.1:
            pos_votes += 1; pos_why.append(f"DXY {chg:.2f}% tailwind")
    except Exception:
        pass

    exp = get_expectation()
    exp_votes, exp_why = exp["votes"], exp["why"]

    # Conflict if positioning disagrees with net expectation OR with any single
    # key release in the cluster (e.g. PPI hot-bearish vs Retail Sales cold-bullish
    # net to 0 — a bullish position still conflicts with the PPI leg).
    _any_disagree = any(
        pos_votes != 0 and d.get("votes", 0) != 0
        and (pos_votes > 0) != (d["votes"] > 0)
        for d in exp.get("details", [])
    )
    conflict = (
        pos_votes != 0 and exp_votes != 0
        and (pos_votes > 0) != (exp_votes > 0)
    ) or _any_disagree
    total = pos_votes + exp_votes

    if conflict:
        label, action = "Neutral (conflict — WAIT)", "WAIT"
    elif total >= 3:
        label, action = "Bullish (confirmed)", "BUY"
    elif total == 2:
        label, action = "Bullish (weak)", "BUY"
    elif total <= -3:
        label, action = "Bearish (confirmed)", "SELL"
    elif total == -2:
        label, action = "Bearish (weak)", "SELL"
    else:
        # ±1 or 0 → WAIT (was BUY/SELL before, overconfident)
        label, action = "Neutral", "WAIT"

    why = (
        [f"Expect: {w}" for w in exp_why]
        + [f"Pos: {w}" for w in pos_why]
        + (["conflict: tech vs consensus disagree -> WAIT"] if conflict else [])
    )
    return {
        "label": label, "action": action, "votes": total, "why": why,
        "positioning": {"votes": pos_votes, "why": pos_why},
        "expectation": {"votes": exp_votes, "why": exp_why, "events": exp["events"]},
        "conflict": conflict,
    }
