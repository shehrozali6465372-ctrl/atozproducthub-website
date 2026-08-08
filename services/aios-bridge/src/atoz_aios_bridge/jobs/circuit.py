"""Circuit breaker stub (API Contracts §7: 50% failures / 60s recovery).

M3 ships the state machine; metrics export and half-open probing wire up
with the observability phase.
"""

import time


class CircuitBreaker:
    """Trip after ``failure_threshold`` consecutive failures; recovers after timeout."""

    def __init__(self, *, failure_threshold: int = 5, recovery_timeout: float = 60.0) -> None:
        self._threshold = max(1, failure_threshold)
        self._recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        return time.time() - self._opened_at < self._recovery_timeout

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = time.time()

    def reset(self) -> None:
        self._failures = 0
        self._opened_at = None
