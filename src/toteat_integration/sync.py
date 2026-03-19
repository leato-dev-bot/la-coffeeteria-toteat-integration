from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .client import ToteatClient
from .config import Settings
from .db import (
    finish_run,
    init_db,
    load_successful_windows,
    record_failed_task,
    record_success_checkpoint,
    start_run,
    store_raw,
)
from .endpoints import ENDPOINTS
from .progress import write_progress
from .timeutils import chunk_date_range, fmt, today_in_tz


def _date_params(defn: dict[str, Any], start, end):
    names = defn.get("params", ())
    date_format = defn.get("date_format", "%Y%m%d")
    if len(names) == 1:
        return {names[0]: fmt(start, date_format)}
    if len(names) == 2:
        return {names[0]: fmt(start, date_format), names[1]: fmt(end, date_format)}
    return {}


def _progress_payload(settings: Settings, mode: str, start_date, end_date, total_tasks: int, completed_tasks: int, rows: int, run_id: int, current_endpoint=None, current_window_start=None, current_window_end=None, status: str = "running", error: str | None = None):
    payload = {
        "status": status,
        "mode": mode,
        "tenant_id": settings.tenant_id,
        "timezone": settings.timezone_name,
        "start_date": start_date,
        "end_date": end_date,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "rows_loaded": rows,
        "current_endpoint": current_endpoint,
        "current_window_start": current_window_start,
        "current_window_end": current_window_end,
        "run_id": run_id,
        "updated_at": datetime.now(settings.timezone),
    }
    if error:
        payload["error"] = error
    return payload


def run_sync(conn, settings: Settings, mode: str, start_date=None, end_date=None, exclude_endpoints: list[str] | None = None) -> int:
    init_db(conn, settings)
    client = ToteatClient(settings)
    run_id = start_run(conn, settings, mode)
    rows = 0
    total_tasks = 0
    completed_tasks = 0
    current_endpoint = None
    current_window_start = None
    current_window_end = None

    try:
        today = today_in_tz(settings.timezone)
        if mode == "daily":
            start_date = end_date = today - timedelta(days=1)
        elif mode == "backfill":
            end_date = today
            start_date = today - timedelta(days=365 * 3)
        elif mode == "range":
            if not (start_date and end_date):
                raise ValueError("range mode requires start_date and end_date")
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        exclude = set(exclude_endpoints or [])
        successful_windows = load_successful_windows(conn, settings)
        tasks = []

        for key, defn in sorted(ENDPOINTS.items(), key=lambda item: item[1].get("priority", 999)):
            if key in exclude:
                continue
            endpoint_mode = defn["mode"]
            if endpoint_mode == "full":
                tasks.append((key, defn, None, None))
            elif endpoint_mode == "daily":
                cursor = start_date
                while cursor <= end_date:
                    tasks.append((key, defn, cursor, cursor))
                    cursor += timedelta(days=1)
            elif endpoint_mode == "range":
                for chunk_start, chunk_end in chunk_date_range(start_date, end_date, defn.get("window_days", 15)):
                    tasks.append((key, defn, chunk_start, chunk_end))

        filtered_tasks = []
        for key, defn, window_start, window_end in tasks:
            signature = (key, window_start.isoformat() if window_start else None, window_end.isoformat() if window_end else None)
            if signature not in successful_windows:
                filtered_tasks.append((key, defn, window_start, window_end))

        tasks = filtered_tasks
        total_tasks = len(tasks)
        write_progress(_progress_payload(settings, mode, start_date, end_date, total_tasks, completed_tasks, rows, run_id))

        failed_count = 0
        last_error = None
        for key, defn, window_start, window_end in tasks:
            current_endpoint = key
            current_window_start = window_start
            current_window_end = window_end
            write_progress(_progress_payload(settings, mode, start_date, end_date, total_tasks, completed_tasks, rows, run_id, current_endpoint, current_window_start, current_window_end))

            endpoint_mode = defn["mode"]
            if endpoint_mode == "full":
                params = dict(defn.get("extra", {}))
                business_date = None
                checkpoint_end = None
            else:
                params = _date_params(defn, window_start, window_end)
                params.update(defn.get("extra", {}))
                business_date = window_start
                checkpoint_end = window_end

            try:
                payload = client.get(defn["path"], params)
                rows += store_raw(conn, settings, key, params, business_date, payload)
                record_success_checkpoint(conn, settings, key, business_date, checkpoint_end)
            except Exception as task_exc:
                failed_count += 1
                last_error = str(task_exc)
                record_failed_task(conn, settings, key, params, business_date, checkpoint_end, str(task_exc))
            finally:
                completed_tasks += 1
                write_progress(_progress_payload(settings, mode, start_date, end_date, total_tasks, completed_tasks, rows, run_id, current_endpoint, current_window_start, current_window_end))

        final_status = "success" if failed_count == 0 else "partial_success"
        finish_run(conn, run_id, final_status, rows, last_error)
        write_progress(_progress_payload(settings, mode, start_date, end_date, total_tasks, completed_tasks, rows, run_id, status=final_status, error=last_error))
        return rows
    except Exception as exc:
        finish_run(conn, run_id, "failed", rows, str(exc))
        write_progress(_progress_payload(settings, mode, start_date, end_date, total_tasks, completed_tasks, rows, run_id, current_endpoint, current_window_start, current_window_end, status="failed", error=str(exc)))
        raise
