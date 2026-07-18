from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable


class FixedWindowRateLimiter:
    def __init__(
        self,
        *,
        limit: int = 5,
        window_seconds: float = 600,
        clock: Callable[[], float] = time.time,
    ):
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self.clock()
        cutoff = now - self.window_seconds
        entries = self._requests[key]
        while entries and entries[0] <= cutoff:
            entries.popleft()
        if len(entries) >= self.limit:
            return False
        entries.append(now)
        return True
