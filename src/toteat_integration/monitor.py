from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROGRESS_FILE = Path("runtime/progress.json")


def load_progress() -> dict[str, Any] | None:
    if not PROGRESS_FILE.exists():
        return None
    return json.loads(PROGRESS_FILE.read_text())


def build_status_summary(conn) -> dict[str, Any]:
    summary: dict[str, Any] = {"progress": load_progress() or {}}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT endpoint_key, count(*)
            FROM toteat.raw_api_responses
            GROUP BY endpoint_key
            ORDER BY endpoint_key
            """
        )
        summary["raw_counts"] = {endpoint: count for endpoint, count in cur.fetchall()}

        cur.execute(
            """
            SELECT endpoint_key, count(*)
            FROM toteat.failed_tasks
            WHERE resolved_at IS NULL
            GROUP BY endpoint_key
            ORDER BY endpoint_key
            """
        )
        summary["open_failed_tasks"] = {endpoint: count for endpoint, count in cur.fetchall()}

        cur.execute(
            """
            SELECT endpoint_key, max(window_end)
            FROM toteat.endpoint_checkpoints
            WHERE status = 'success'
            GROUP BY endpoint_key
            ORDER BY endpoint_key
            """
        )
        summary["last_success_window_end"] = {endpoint: str(window_end) for endpoint, window_end in cur.fetchall()}
    return summary
