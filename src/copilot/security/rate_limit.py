"""
Per-key sliding-window rate limiter. In memory, fine for one replica; Redis is the multi-
replica upgrade.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self._limit = limit_per_minute
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key_id: str) -> tuple[bool, int]:
        """Returns (allowed, retry_after_seconds)."""
        now = time.monotonic()
        window = self._events[key_id]
        while window and now - window[0] > 60.0:
            window.popleft()
        if len(window) >= self._limit:
            return False, int(60.0 - (now - window[0])) + 1
        window.append(now)
        return True, 0
