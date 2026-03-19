from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def today_in_tz(tz: ZoneInfo) -> date:
    return datetime.now(tz).date()


def chunk_date_range(start: date, end: date, chunk_days: int):
    cursor = start
    while cursor <= end:
        chunk_end = min(end, cursor + timedelta(days=chunk_days - 1))
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


def fmt(date_value: date, pattern: str = "%Y%m%d") -> str:
    return date_value.strftime(pattern)
