"""Free high-impact USD news calendar (ForexFactory/FairEconomy XML, no key).

Strategy: can NOT predict CPI/FOMC/NFP direction. Instead: blackout new
signals around releases + show countdown banner.
"""
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from config import DATA_DIR

CACHE = DATA_DIR / "news_cache.json"
URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
_LAST_SOURCE = "unknown"


def last_source() -> str:
    return _LAST_SOURCE

KEYWORDS = ("CPI", "NFP", "Non-Farm", "FOMC", "Fed ", "Powell", "PPI",
            "Retail Sales", "ISM", "Payrolls", "Unemployment", "Interest Rate",
            "PCE", "GDP")


def _parse_time(date_s: str, time_s: str) -> datetime | None:
    """FF XML times are UTC wall-clock (verified: '12:30pm' = 12:30 UTC CPI release).

    Earlier ET-assumption (+4h) was wrong and shifted every event 4h late.
    """
    try:
        dt = datetime.strptime(f"{date_s} {time_s}", "%m-%d-%Y %I:%M%p")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def update_calendar() -> list[dict]:
    r = requests.get(URL, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    root = ET.fromstring(r.content)
    events = []
    for ev in root.findall("event"):
        country = (ev.findtext("country") or "").strip()
        impact = (ev.findtext("impact") or "").strip()
        title = (ev.findtext("title") or "").strip()
        if country != "USD" or impact != "High":
            continue
        ts = _parse_time((ev.findtext("date") or "").strip(), (ev.findtext("time") or "").strip())
        if ts is None:
            continue
        events.append({
            "title": title, "time_utc": ts.isoformat(),
            "forecast": (ev.findtext("forecast") or "").strip(),
            "previous": (ev.findtext("previous") or "").strip(),
            "key": any(k.lower() in title.lower() for k in KEYWORDS),
        })
    events.sort(key=lambda e: e["time_utc"])
    CACHE.write_text(json.dumps({"v": 2, "updated": datetime.now(timezone.utc).isoformat(), "events": events}))
    print(f"News: {len(events)} high-impact USD events cached")
    return events


def _fallback() -> list[dict]:
    global _LAST_SOURCE
    try:
        fb = json.loads((Path(__file__).parent / "news_fallback.json").read_text())
        _LAST_SOURCE = "bundled snapshot"
        return fb["events"]
    except Exception:
        return []


def load_events(max_age_h: int = 24 * 7) -> list[dict]:
    global _LAST_SOURCE
    try:
        cache = json.loads(CACHE.read_text())
        if cache.get("v") != 2:
            raise ValueError("stale calendar schema")
        age = datetime.now(timezone.utc) - datetime.fromisoformat(cache["updated"])
        if age < timedelta(hours=max_age_h):
            _LAST_SOURCE = f"cache ({int(age.total_seconds() // 3600)}h old)"
            return cache["events"]
    except Exception:
        pass
    try:
        evs = update_calendar()
        _LAST_SOURCE = "live XML"
        return evs
    except Exception as e:
        print(f"News fetch failed (non-fatal, using fallback): {e}")
        _LAST_SOURCE = f"fallback ({e})"
        try:
            evs = json.loads(CACHE.read_text())["events"]
            if evs:
                _LAST_SOURCE = "stale cache (live failed)"
                return evs
        except Exception:
            pass
        return _fallback()


def status(now: datetime | None = None, pre_min: int = 30, post_min: int = 30) -> dict:
    """Return blackout state + next event for gates/banner."""
    now = now or datetime.now(timezone.utc)
    events = load_events()
    upcoming = [e for e in events if datetime.fromisoformat(e["time_utc"]) > now - timedelta(minutes=post_min)]
    nxt = min(upcoming, key=lambda e: e["time_utc"]) if upcoming else None
    blocked_title, mins = None, None
    for e in events:
        t = datetime.fromisoformat(e["time_utc"])
        delta_min = (t - now).total_seconds() / 60
        if -post_min <= delta_min <= pre_min:
            blocked_title, mins = e["title"], delta_min
            break
    return {"blocked": blocked_title is not None, "title": blocked_title,
            "mins_to": round(mins, 0) if mins is not None else None,
            "next": nxt}


# --- Provisional scheduled calendar (display only, never blocks signals) ---
# NFP ≈ first Friday monthly 12:30 UTC; FOMC decisions per published Fed schedule.
# Dates can shift (shutdowns, reschedules) — tagged provisional until weekly XML confirms.
FOMC_DECISIONS_2026 = ["2026-10-28", "2026-12-09"]


def scheduled_future(now: datetime | None = None, months: int = 3) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    out = []
    y, m = now.year, now.month
    for _ in range(months):
        first = datetime(y, m, 1, tzinfo=timezone.utc)
        # first Friday: weekday() Mon=0..Fri=4
        nfp = first + timedelta(days=(4 - first.weekday()) % 7)
        t = nfp.replace(hour=12, minute=30)
        if t > now:
            out.append({"title": "NFP / Non-Farm Payrolls", "time_utc": t.isoformat(),
                        "forecast": "", "previous": "", "key": True, "provisional": True})
        m += 1
        if m > 12:
            m, y = 1, y + 1
    for d in FOMC_DECISIONS_2026:
        t = datetime.strptime(d, "%Y-%m-%d").replace(hour=18, minute=0, tzinfo=timezone.utc)
        if t > now:
            out.append({"title": "FOMC Rate Decision", "time_utc": t.isoformat(),
                        "forecast": "", "previous": "", "key": True, "provisional": True})
    return sorted(out, key=lambda e: e["time_utc"])
