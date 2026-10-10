"""In-memory per-IP rate limiter for POST /api/route (AGENTS.md B8)."""

import time
from collections import defaultdict


class InMemoryRateLimiter:
    """Sliding-window per-IP rate limiter."""

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self._history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0

        # Filter out timestamps older than 60s
        timestamps = [ts for ts in self._history[client_ip] if ts > window_start]
        if len(timestamps) >= self.requests_per_minute:
            self._history[client_ip] = timestamps
            return False

        timestamps.append(now)
        self._history[client_ip] = timestamps
        return True


rate_limiter = InMemoryRateLimiter()
