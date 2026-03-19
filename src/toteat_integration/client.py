from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from typing import Any

from .config import Settings


class ToteatClient:
    def __init__(self, settings: Settings, requests_per_minute: int = 3, max_retries: int = 8):
        self.settings = settings
        self.requests_per_minute = requests_per_minute
        self.max_retries = max_retries
        self.request_timestamps: deque[float] = deque()

    def _base_params(self) -> dict[str, str]:
        return {
            "xir": self.settings.xir,
            "xil": self.settings.xil,
            "xiu": self.settings.xiu,
            "xapitoken": self.settings.xapitoken,
        }

    def _wait_for_slot(self) -> None:
        now = time.time()
        while self.request_timestamps and now - self.request_timestamps[0] >= 60:
            self.request_timestamps.popleft()
        if len(self.request_timestamps) >= self.requests_per_minute:
            sleep_for = 60 - (now - self.request_timestamps[0]) + 1
            if sleep_for > 0:
                time.sleep(sleep_for)
        now = time.time()
        while self.request_timestamps and now - self.request_timestamps[0] >= 60:
            self.request_timestamps.popleft()

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = self._base_params()
        if params:
            query.update({k: str(v) for k, v in params.items() if v is not None})
        url = f"{self.settings.toteat_base_url}/{path}?{urllib.parse.urlencode(query)}"

        attempt = 0
        while True:
            self._wait_for_slot()
            try:
                with urllib.request.urlopen(url, timeout=60) as response:
                    payload = response.read().decode("utf-8", "replace")
                self.request_timestamps.append(time.time())
                return json.loads(payload)
            except urllib.error.HTTPError as exc:
                self.request_timestamps.append(time.time())
                if exc.code == 429 and attempt < self.max_retries:
                    retry_after = exc.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        sleep_for = int(retry_after)
                    else:
                        sleep_for = min(300, (2 ** attempt) * 20)
                    time.sleep(sleep_for)
                    attempt += 1
                    continue
                raise
