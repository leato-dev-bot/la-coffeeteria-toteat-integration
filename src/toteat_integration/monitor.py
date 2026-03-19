from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROGRESS_FILE = Path("runtime/progress.json")


def load_progress() -> dict[str, Any] | None:
    if not PROGRESS_FILE.exists():
        return None
    return json.loads(PROGRESS_FILE.read_text())
