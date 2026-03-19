from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any

import psycopg

from .config import Settings


@contextmanager
def connect(settings: Settings):
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(f"SET TIME ZONE '{settings.timezone_name}'")
        yield conn


def init_db(conn, settings: Settings) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO toteat.tenants (tenant_id, tenant_name, db_name, timezone, locale)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id) DO UPDATE SET
              tenant_name = EXCLUDED.tenant_name,
              db_name = EXCLUDED.db_name,
              timezone = EXCLUDED.timezone,
              locale = EXCLUDED.locale,
              updated_at = now()
            """,
            [settings.tenant_id, settings.tenant_name, settings.db_name, settings.timezone_name, settings.locale],
        )
    conn.commit()


def start_run(conn, settings: Settings, mode: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO toteat.ingestion_runs (tenant_id, mode) VALUES (%s, %s) RETURNING run_id",
            [settings.tenant_id, mode],
        )
        run_id = cur.fetchone()[0]
    conn.commit()
    return run_id


def finish_run(conn, run_id: int, status: str, rows_loaded: int, error_message: str | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE toteat.ingestion_runs SET finished_at = now(), status = %s, rows_loaded = %s, error_message = %s WHERE run_id = %s",
            [status, rows_loaded, error_message, run_id],
        )
    conn.commit()


def store_raw(conn, settings: Settings, endpoint_key: str, request_params: dict[str, Any], business_date, payload: Any) -> int:
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    request_params_json = json.dumps(request_params, sort_keys=True)
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO toteat.raw_api_responses (tenant_id, endpoint_key, request_params, business_date, response_payload, payload_hash)
            VALUES (%s, %s, %s::jsonb, %s, %s::jsonb, %s)
            """,
            [settings.tenant_id, endpoint_key, request_params_json, business_date, payload_json, payload_hash],
        )
        cur.execute(
            """
            UPDATE toteat.failed_tasks
            SET resolved_at = now()
            WHERE tenant_id = %s
              AND endpoint_key = %s
              AND business_date IS NOT DISTINCT FROM %s
              AND request_params::text = %s
              AND resolved_at IS NULL
            """,
            [settings.tenant_id, endpoint_key, business_date, request_params_json],
        )
    conn.commit()
    return 1


def record_failed_task(conn, settings: Settings, endpoint_key: str, request_params: dict[str, Any], business_date, window_end, error_message: str) -> None:
    request_params_json = json.dumps(request_params, sort_keys=True)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO toteat.failed_tasks (tenant_id, endpoint_key, business_date, request_params, error_message, retry_count)
            VALUES (%s, %s, %s, %s::jsonb, %s, 1)
            ON CONFLICT ((tenant_id), (endpoint_key), (business_date), (md5(request_params::text))) WHERE resolved_at IS NULL
            DO UPDATE SET
              error_message = EXCLUDED.error_message,
              retry_count = toteat.failed_tasks.retry_count + 1,
              last_failed_at = now()
            """,
            [settings.tenant_id, endpoint_key, business_date, request_params_json, error_message],
        )
        cur.execute(
            """
            INSERT INTO toteat.endpoint_checkpoints (tenant_id, endpoint_key, window_start, window_end, status, error_message)
            VALUES (%s, %s, %s, %s, 'failed', %s)
            ON CONFLICT (tenant_id, endpoint_key, window_start, window_end)
            DO UPDATE SET
              status = 'failed',
              error_message = EXCLUDED.error_message,
              updated_at = now()
            """,
            [settings.tenant_id, endpoint_key, business_date, window_end, error_message],
        )
    conn.commit()


def record_success_checkpoint(conn, settings: Settings, endpoint_key: str, window_start, window_end) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO toteat.endpoint_checkpoints (tenant_id, endpoint_key, window_start, window_end, status, error_message)
            VALUES (%s, %s, %s, %s, 'success', NULL)
            ON CONFLICT (tenant_id, endpoint_key, window_start, window_end)
            DO UPDATE SET
              status = 'success',
              error_message = NULL,
              updated_at = now()
            """,
            [settings.tenant_id, endpoint_key, window_start, window_end],
        )
    conn.commit()


def load_successful_windows(conn, settings: Settings) -> set[tuple[str, str | None, str | None]]:
    windows: set[tuple[str, str | None, str | None]] = set()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT endpoint_key, window_start, window_end
            FROM toteat.endpoint_checkpoints
            WHERE tenant_id = %s AND status = 'success'
            """,
            [settings.tenant_id],
        )
        for endpoint_key, window_start, window_end in cur.fetchall():
            windows.add((endpoint_key, window_start.isoformat() if window_start else None, window_end.isoformat() if window_end else None))
    return windows
