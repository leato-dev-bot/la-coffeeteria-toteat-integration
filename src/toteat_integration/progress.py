from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

PROGRESS_FILE = Path("runtime/progress.json")


def _default_serializer(value: Any):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Not serializable: {type(value)!r}")


def write_progress(payload: dict[str, Any]) -> None:
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_default_serializer) + "\n")
