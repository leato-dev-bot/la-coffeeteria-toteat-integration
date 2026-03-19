from __future__ import annotations

from datetime import timedelta
from typing import Any

from .client import ToteatClient
from .config import Settings
from .db import finish_run, init_db, start_run, store_raw
from .endpoints import ENDPOINTS
from .timeutils import chunk_date_range, fmt, today_in_tz


def _date_params(defn: dict[str, Any], start, end):
    names = defn.get("params", ())
    date_format = defn.get("date_format", "%Y%m%d")
    if len(names) == 1:
        return {names[0]: fmt(start, date_format)}
    if len(names) == 2:
        return {names[0]: fmt(start, date_format), names[1]: fmt(end, date_format)}
    return {}


def run_sync(conn, settings: Settings, mode: str, start_date=None, end_date=None) -> int:
    init_db(conn, settings)
    client = ToteatClient(settings)
    run_id = start_run(conn, settings, mode)
    rows = 0
    try:
        today = today_in_tz(settings.timezone)
        if mode == 'daily':
            start_date = end_date = today - timedelta(days=1)
        elif mode == 'backfill':
            end_date = today
            start_date = today - timedelta(days=365 * 3)
        elif mode == 'range':
            if not (start_date and end_date):
                raise ValueError('range mode requires start_date and end_date')
        else:
            raise ValueError(f'Unsupported mode: {mode}')

        for key, defn in ENDPOINTS.items():
            endpoint_mode = defn['mode']
            if endpoint_mode == 'full':
                params = dict(defn.get('extra', {}))
                payload = client.get(defn['path'], params)
                rows += store_raw(conn, settings, key, params, None, payload)
                continue
            if endpoint_mode == 'daily':
                cursor = start_date
                while cursor <= end_date:
                    params = _date_params(defn, cursor, cursor)
                    params.update(defn.get('extra', {}))
                    payload = client.get(defn['path'], params)
                    rows += store_raw(conn, settings, key, params, cursor, payload)
                    cursor += timedelta(days=1)
                continue
            if endpoint_mode == 'range':
                for chunk_start, chunk_end in chunk_date_range(start_date, end_date, defn.get('window_days', 15)):
                    params = _date_params(defn, chunk_start, chunk_end)
                    params.update(defn.get('extra', {}))
                    payload = client.get(defn['path'], params)
                    rows += store_raw(conn, settings, key, params, chunk_start, payload)
                continue
        finish_run(conn, run_id, 'success', rows)
        return rows
    except Exception as exc:
        finish_run(conn, run_id, 'failed', rows, str(exc))
        raise
