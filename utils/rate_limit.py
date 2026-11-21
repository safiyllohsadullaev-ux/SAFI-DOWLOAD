from __future__ import annotations

import time
from collections import defaultdict, deque

from config import RATE_LIMIT_PER_MINUTE


class RateLimiter:
    def __init__(self, limit: int = RATE_LIMIT_PER_MINUTE, window: int = 60) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    def hit(self, user_id: int) -> float:
        """Return seconds to wait. 0 means allowed."""
        now = time.monotonic()
        q = self._hits[user_id]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return max(1.0, self.window - (now - q[0]))
        q.append(now)
        return 0.0


limiter = RateLimiter()
