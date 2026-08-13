"""Retry policy math and idempotency-key helpers (Task 20 §4–§5).

Pure business computation: exponential backoff with jitter for the durable
queue ledger and job runs, plus deterministic idempotency keys. No state,
no AI. Used by the service layer and unit-tested directly.
"""

import hashlib
import random
from datetime import UTC, datetime, timedelta


def next_retry_at(
    *,
    attempts: int,
    max_attempts: int,
    base_delay_seconds: float = 30.0,
    max_delay_seconds: float = 86400.0,
    jitter: float = 0.1,
    now: datetime | None = None,
) -> datetime | None:
    """Compute the next retry time using exponential backoff + jitter.

    ``attempts`` is the completed attempt count (0-based after a claim).
    Returns ``None`` when ``attempts >= max_attempts`` or the schedule is
    disabled (``max_attempts <= 0``) — the item/job is then terminal.
    Delay is ``base * 2 ** (attempts - 1)`` bounded by ``max_delay_seconds``,
    then uniformly jittered by ``±jitter`` (never negative).
    """
    if max_attempts <= 0 or attempts >= max_attempts:
        return None
    delay = min(base_delay_seconds * (2 ** max(0, attempts - 1)), max_delay_seconds)
    if jitter > 0:
        delay = max(0.0, delay * (1.0 + random.uniform(-jitter, jitter)))
    return (now or datetime.now(UTC)) + timedelta(seconds=delay)


def idempotency_key(*parts: str) -> str:
    """Deterministic idempotency key from stable parts (sha256 hex).

    Callers combine a stable business seed (e.g. rule id + trigger ref) so
    replay deliveries resolve to the same key and the same persisted record.
    """
    hasher = hashlib.sha256()
    for part in parts:
        hasher.update(part.encode("utf-8"))
        hasher.update(b"\x00")
    return hasher.hexdigest()
