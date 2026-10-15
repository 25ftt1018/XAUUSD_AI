"""Market-open + freshness + spot-deviation guards.

Gold (spot/futures) is closed:
- Saturday all day (UTC)
- Sunday before ~22:00 UTC
- Friday after ~21:00 UTC
- Daily maintenance break ~21:00-22:00 UTC

Yahoo GC=F keeps returning the last closed candle while shut, so any
signal built on it is stale. These helpers let signal + cron refuse
to send actionable entries off old data.
"""
from datetime import datetime, timezone

# Max age of the last CLOSED candle before data counts as stale.
MAX_AGE_H1_H = 2.5
MAX_AGE_H4_H = 6.0
# Futures (GC=F) vs spot LIVe deviation that marks entry untradable.
SPOT_MAX_DIFF_ABS = 12.0  # USD; floor, relaxed by 0.5*ATR


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_market_open(now: datetime | None = None) -> tuple[bool, str]:
    now = now or now_utc()
    dow = now.weekday()  # Mon=0 .. Sat=5 Sun=6
    if dow == 5:
        return False, "market closed (Saturday)"
    if dow == 6 and now.hour < 22:
        return False, "market closed (Sunday pre-open)"
    if dow == 4 and now.hour >= 21:
        return False, "market closed (Friday close)"
    if now.hour == 21:
        return False, "market closed (daily break 21-22 UTC)"
    return True, "open"


def candle_age_hours(candle_time, now: datetime | None = None) -> float:
    now = now or now_utc()
    try:
        import pandas as pd
        ts = pd.to_datetime(candle_time, utc=True).to_pydatetime()
    except Exception:
        return 999.0
    return (now - ts).total_seconds() / 3600.0


def check_fresh(candle_time, max_age_h: float, now: datetime | None = None) -> tuple[bool, str]:
    age = candle_age_hours(candle_time, now)
    if age > max_age_h:
        return False, f"stale data: last candle {age:.1f}h old (> {max_age_h}h)"
    return True, "fresh"


def check_spot(entry: float, spot: float | None, atr: float | None) -> tuple[bool, str]:
    """Futures entry vs live spot. None spot = can't verify -> pass open."""
    if spot is None:
        return True, "spot unavailable"
    try:
        diff = abs(float(entry) - float(spot))
    except Exception:
        return True, "spot unavailable"
    limit = SPOT_MAX_DIFF_ABS
    if atr:
        try:
            limit = max(limit, float(atr) * 0.5)
        except Exception:
            pass
    if diff > limit:
        return False, f"entry far from spot: futures {entry:.2f} vs spot {spot:.2f} (diff ${diff:.2f} > ${limit:.0f})"
    return True, "spot ok"
