"""Per-account rate limiting for Pinterest API calls.

Pinterest documents org_read and org_write rate-limit categories; a single
global queue would let one account's throttle starve the other nine, so
every account gets its own token bucket per category (M6 scope, API
Contracts §7). Retries use exponential backoff with jitter, and 429s are
recorded per account (never shared).
"""

import asyncio
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field

from atoz_pinterest_service.domain.enums import RemoteErrorKind


@dataclass
class TokenBucket:
    """Leaky token bucket for one (account, category) budget."""

    capacity: float
    refill_per_second: float
    tokens: float = 0.0
    updated_at: float = field(default_factory=time.monotonic)

    async def acquire(self) -> None:
        """Wait until a token is available (per-account, per-category)."""
        while True:
            now = time.monotonic()
            elapsed = now - self.updated_at
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
            self.updated_at = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            await asyncio.sleep((1.0 - self.tokens) / self.refill_per_second)


class PerAccountRateLimiter:
    """Token buckets keyed by (account_id, category) — never global."""

    def __init__(self, *, read_per_minute: int, write_per_minute: int) -> None:
        self._buckets: dict[tuple[str, str], TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=1.0, refill_per_second=1.0)
        )
        self._read_per_minute = read_per_minute
        self._write_per_minute = write_per_minute

    def _bucket(self, account_id: str, category: str) -> TokenBucket:
        if category == "org_write":
            capacity = float(self._write_per_minute)
        else:
            capacity = float(self._read_per_minute)
        bucket = self._buckets[(account_id, category)]
        bucket.capacity = capacity
        bucket.refill_per_second = capacity / 60.0
        return bucket

    async def acquire(self, account_id: str, category: str) -> None:
        """Block until this account's budget allows the call."""
        await self._bucket(account_id, category).acquire()


def backoff_delay(*, attempt: int, base: float = 1.0, max_delay: float = 30.0) -> float:
    """Exponential backoff with full jitter: delay ∈ [0, base * 2^attempt]."""
    cap = min(max_delay, base * (2**attempt))
    return random.uniform(0.0, cap)


def classify_http_error(
    status_code: int | None, *, retryable_transport: bool = True
) -> RemoteErrorKind:
    """Classify a Pinterest API failure into a retry decision."""
    if status_code is None:
        return RemoteErrorKind.NETWORK if retryable_transport else RemoteErrorKind.VALIDATION
    if status_code == 401:
        return RemoteErrorKind.UNAUTHORIZED
    if status_code == 403:
        return RemoteErrorKind.FORBIDDEN
    if status_code == 404:
        return RemoteErrorKind.NOT_FOUND
    if status_code == 429:
        return RemoteErrorKind.RATE_LIMITED
    if 500 <= status_code < 600:
        return RemoteErrorKind.SERVER_ERROR
    return RemoteErrorKind.VALIDATION


def is_retryable(kind: RemoteErrorKind) -> bool:
    """Which error kinds may be retried safely (Task 16: retry only safe ops)."""
    return kind in {
        RemoteErrorKind.RATE_LIMITED,
        RemoteErrorKind.SERVER_ERROR,
        RemoteErrorKind.NETWORK,
    }
