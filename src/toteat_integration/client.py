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
    def __init__(self, settings: Settings, requests_per_minute: int | None = None, max_retries: int = 8):
        self.settings = settings
        self.requests_per_minute = requests_per_minute or settings.requests_per_minute_start
        self.max_retries = max_retries
        self.request_timestamps: deque[float] = deque()
        self.legacy_base_url = "https://toteatglobal.appspot.com/mw/or/1.0"
        self.success_streak = 0

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

    def _fetch_json(self, url: str) -> dict[str, Any]:
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = response.read().decode("utf-8", "replace")
        return json.loads(payload)

    def _register_success(self) -> None:
        self.success_streak += 1
        if self.success_streak >= self.settings.requests_ramp_step_successes and self.requests_per_minute < self.settings.requests_per_minute_max:
            self.requests_per_minute += 1
            self.success_streak = 0

    def _register_failure(self) -> None:
        self.success_streak = 0
        if self.requests_per_minute > self.settings.requests_per_minute_start:
            self.requests_per_minute -= 1

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = self._base_params()
        if params:
            query.update({k: str(v) for k, v in params.items() if v is not None})
        base_url = self.legacy_base_url if path == "collection" else self.settings.toteat_base_url
        url = f"{base_url}/{path}?{urllib.parse.urlencode(query)}"
        legacy_url = f"{self.legacy_base_url}/{path}?{urllib.parse.urlencode(query)}"

        attempt = 0
        while True:
            self._wait_for_slot()
            try:
                data = self._fetch_json(url)
                self.request_timestamps.append(time.time())
                self._register_success()
                return data
            except urllib.error.HTTPError as exc:
                self.request_timestamps.append(time.time())
                self._register_failure()
                if path != "collection" and exc.code == 500:
                    try:
                        self._wait_for_slot()
                        data = self._fetch_json(legacy_url)
                        self.request_timestamps.append(time.time())
                        self._register_success()
                        return data
                    except urllib.error.HTTPError as legacy_exc:
                        self.request_timestamps.append(time.time())
                        self._register_failure()
                        exc = legacy_exc
                if exc.code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    retry_after = exc.headers.get("Retry-After") if hasattr(exc, "headers") else None
                    if retry_after and str(retry_after).isdigit():
                        sleep_for = int(retry_after)
                    else:
                        sleep_for = min(600, (2**attempt) * 20)
                    time.sleep(sleep_for)
                    attempt += 1
                    continue
                raise
