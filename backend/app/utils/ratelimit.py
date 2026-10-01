from __future__ import annotations

import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._events: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, key: int, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        events = self._events[key]
        while events and events[0] <= current - self.window:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(current)
        return True

