import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl = ttl_seconds
        self._entry: tuple[float, Any] | None = None

    def set(self, value: Any) -> None:
        self._entry = (time.monotonic(), value)

    def get_fresh(self) -> Any | None:
        if self._entry is None:
            return None
        ts, value = self._entry
        if time.monotonic() - ts < self.ttl:
            return value
        return None

    def get_any(self) -> Any | None:
        if self._entry is None:
            return None
        return self._entry[1]