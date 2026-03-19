from datetime import date
from zoneinfo import ZoneInfo

from toteat_integration.timeutils import chunk_date_range, fmt, today_in_tz


def test_chunk_date_range():
    chunks = list(chunk_date_range(date(2026, 3, 1), date(2026, 3, 20), 15))
    assert chunks == [(date(2026, 3, 1), date(2026, 3, 15)), (date(2026, 3, 16), date(2026, 3, 20))]


def test_fmt():
    assert fmt(date(2026, 3, 19)) == '20260319'
    assert fmt(date(2026, 3, 19), '%Y-%m-%d') == '2026-03-19'


def test_today_in_tz_returns_date():
    assert hasattr(today_in_tz(ZoneInfo('America/Santiago')), 'year')
