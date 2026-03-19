from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from .config import Settings


class ToteatClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _base_params(self) -> dict[str, str]:
        return {
            "xir": self.settings.xir,
            "xil": self.settings.xil,
            "xiu": self.settings.xiu,
            "xapitoken": self.settings.xapitoken,
        }

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = self._base_params()
        if params:
            query.update({k: str(v) for k, v in params.items() if v is not None})
        url = f"{self.settings.toteat_base_url}/{path}?{urllib.parse.urlencode(query)}"
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = response.read().decode("utf-8", "replace")
        return json.loads(payload)
