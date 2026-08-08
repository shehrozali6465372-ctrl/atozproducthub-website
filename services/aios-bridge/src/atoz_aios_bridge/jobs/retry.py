"""Retry policy (API Contracts §7): exponential backoff 1s x 2, cap 60s.

Only 429 (respecting Retry-After) and 5xx/network failures are retried;
4xx validation errors fail fast.
"""

import httpx

RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


def backoff_delay(
    attempt: int,
    *,
    base: float = 1.0,
    cap: float = 60.0,
    retry_after: int | None = None,
) -> float:
    """Exponential backoff for the given zero-based attempt."""
    if retry_after is not None:
        return min(float(retry_after), cap)
    return min(cap, base * (2**attempt))


def is_retryable(exc: BaseException) -> bool:
    """True for network errors and 429/5xx responses; False otherwise."""
    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_HTTP_STATUS
    return False


def retry_after_from(exc: BaseException) -> int | None:
    if isinstance(exc, httpx.HTTPStatusError):
        value = exc.response.headers.get("Retry-After")
        if value and value.isdigit():
            return int(value)
    return None
