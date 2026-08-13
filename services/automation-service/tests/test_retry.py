"""Retry-policy math tests (Task 20 §5): exponential backoff + jitter."""

from datetime import UTC, datetime, timedelta

import pytest

from atoz_automation_service.domain.retry import idempotency_key, next_retry_at

BASE = 2.0
MAX_DELAY = 32.0


def _now() -> datetime:
    return datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)


def test_backoff_doubles_per_attempt() -> None:
    now = _now()
    first = next_retry_at(
        attempts=1,
        max_attempts=5,
        base_delay_seconds=BASE,
        max_delay_seconds=MAX_DELAY,
        jitter=0.0,
        now=now,
    )
    second = next_retry_at(
        attempts=2,
        max_attempts=5,
        base_delay_seconds=BASE,
        max_delay_seconds=MAX_DELAY,
        jitter=0.0,
        now=now,
    )
    third = next_retry_at(
        attempts=3,
        max_attempts=5,
        base_delay_seconds=BASE,
        max_delay_seconds=MAX_DELAY,
        jitter=0.0,
        now=now,
    )
    assert first == now + timedelta(seconds=2)
    assert second == now + timedelta(seconds=4)
    assert third == now + timedelta(seconds=8)
    assert first < second < third


def test_backoff_is_capped_at_max_delay() -> None:
    now = _now()
    capped = next_retry_at(
        attempts=10,
        max_attempts=20,
        base_delay_seconds=BASE,
        max_delay_seconds=MAX_DELAY,
        jitter=0.0,
        now=now,
    )
    assert capped == now + timedelta(seconds=MAX_DELAY)


def test_no_retry_when_attempts_exhausted() -> None:
    assert (
        next_retry_at(
            attempts=5, max_attempts=5, base_delay_seconds=BASE, max_delay_seconds=MAX_DELAY
        )
        is None
    )
    assert (
        next_retry_at(
            attempts=4, max_attempts=3, base_delay_seconds=BASE, max_delay_seconds=MAX_DELAY
        )
        is None
    )
    assert (
        next_retry_at(
            attempts=1, max_attempts=0, base_delay_seconds=BASE, max_delay_seconds=MAX_DELAY
        )
        is None
    )
    assert (
        next_retry_at(
            attempts=1, max_attempts=-1, base_delay_seconds=BASE, max_delay_seconds=MAX_DELAY
        )
        is None
    )


def test_jitter_stays_within_bounds_and_non_negative() -> None:
    now = _now()
    delays: list[float] = []
    for _ in range(200):
        scheduled = next_retry_at(
            attempts=1,
            max_attempts=10,
            base_delay_seconds=BASE,
            max_delay_seconds=MAX_DELAY,
            jitter=0.1,
            now=now,
        )
        assert scheduled is not None
        delays.append((scheduled - now).total_seconds())
    assert min(delays) >= 0
    assert max(delays) <= BASE * 1.1
    assert min(delays) >= BASE * 0.9
    assert len(set(delays)) > 1  # jitter actually varies


def test_next_retry_at_is_monotonic_across_attempts() -> None:
    now = _now()
    previous: datetime | None = None
    for attempts in range(1, 6):
        scheduled = next_retry_at(
            attempts=attempts,
            max_attempts=6,
            base_delay_seconds=BASE,
            max_delay_seconds=MAX_DELAY,
            jitter=0.05,
            now=now,
        )
        assert scheduled is not None
        if previous is not None:
            assert scheduled >= previous
        previous = scheduled


def test_idempotency_key_is_deterministic_and_stable() -> None:
    a = idempotency_key("rule:abc", "trigger:42")
    b = idempotency_key("rule:abc", "trigger:42")
    c = idempotency_key("rule:abc", "trigger:43")
    assert a == b
    assert a != c
    assert len(a) == 64
    assert all(ch in "0123456789abcdef" for ch in a)


def test_idempotency_key_differentiates_niche_and_global() -> None:
    assert idempotency_key("n1", "job") != idempotency_key("n2", "job")
    assert idempotency_key("global", "job") != idempotency_key("n1", "job")


@pytest.mark.parametrize(
    ("attempts", "max_attempts", "expected_delta"),
    [(1, 5, 2), (2, 5, 4), (3, 5, 8), (4, 5, 16)],
)
def test_backoff_table(attempts: int, max_attempts: int, expected_delta: int) -> None:
    scheduled = next_retry_at(
        attempts=attempts,
        max_attempts=max_attempts,
        base_delay_seconds=BASE,
        max_delay_seconds=MAX_DELAY,
        jitter=0.0,
        now=_now(),
    )
    assert scheduled == _now() + timedelta(seconds=expected_delta)
