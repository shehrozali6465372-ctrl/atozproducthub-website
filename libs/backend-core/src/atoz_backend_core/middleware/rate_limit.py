"""Rate-limit hooks: in-memory token-bucket store + FastAPI middleware.

Redis-backed enforcement is a future swap behind the same protocol; the
gateway applies per-IP budgets with 429 + ``Retry-After`` (API Contracts §7).
"""

import asyncio
import time
from typing import Protocol

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

EXEMPT_PATHS = ("/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json")


class RateLimitResult:
    __slots__ = ("allowed", "retry_after")

    def __init__(self, allowed: bool, retry_after: int | None = None) -> None:
        self.allowed = allowed
        self.retry_after = retry_after


class RateLimitStore(Protocol):
    """Token-bucket store protocol (in-memory now, Redis later)."""

    async def allow(self, key: str, *, rate: float, burst: int) -> RateLimitResult: ...


class InMemoryTokenBucketStore:
    """Per-key token bucket with async-safe refill."""

    def __init__(self) -> None:
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str, *, rate: float, burst: int) -> RateLimitResult:
        now = time.monotonic()
        async with self._lock:
            tokens, last = self._buckets.get(key, (float(burst), now))
            tokens = min(float(burst), tokens + (now - last) * rate)
            if tokens >= 1.0:
                self._buckets[key] = (tokens - 1.0, now)
                return RateLimitResult(allowed=True)
            self._buckets[key] = (tokens, now)
            if rate > 0:
                retry_after = min(3600, max(1, int((1.0 - tokens) / rate) + 1))
            else:
                retry_after = 60
            return RateLimitResult(allowed=False, retry_after=retry_after)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP token bucket. Exempts liveness/readiness/metrics/docs paths."""

    def __init__(self, app, *, enabled: bool, rate: float, burst: int) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._rate = rate
        self._burst = burst
        self._store = InMemoryTokenBucketStore()

    async def dispatch(self, request: Request, call_next):
        if not self._enabled or request.url.path.startswith(EXEMPT_PATHS):
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        result = await self._store.allow(client_ip, rate=self._rate, burst=self._burst)
        if not result.allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(result.retry_after)},
                content={
                    "type": "about:blank",
                    "title": "Too many requests",
                    "status": 429,
                    "code": "RATE_LIMITED",
                    "detail": "Rate limit exceeded; retry after the Retry-After window.",
                    "retryable": True,
                },
            )
        return await call_next(request)
