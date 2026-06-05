from __future__ import annotations


class TokenBucketRateLimiter:
    def __init__(self, rate_per_second: float, capacity: int) -> None:
        self.rate_per_second = rate_per_second
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.last_refill = 0.0

    def _refill(self, now: float) -> None:
        elapsed = now - self.last_refill
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_second)
        self.last_refill = now

    def try_acquire(self, now: float) -> bool:
        self._refill(now)
        if self.tokens < 1:
            return False
        self.tokens -= 1
        return True
