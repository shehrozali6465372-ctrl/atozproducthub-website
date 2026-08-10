"""Pin domain rules: idempotency, queue lifecycle, publish attempts.

Publishing is a state machine that mirrors Database Blueprint §5.4:

- Pin: draft → queued → publishing → published | failed | deleted | cancelled
- Queue item: queued → claimed → done | failed | cancelled
- Attempt: pending → success | failed | retryable | cancelled

Duplicate prevention uses a deterministic ``checksum`` (SHA-256 over the
account + board + title + destination), enforced by
``UNIQUE (niche_id, pinterest_account_id, checksum)`` at the database and
checked at the repository before enqueue.
"""

import hashlib
import json
from datetime import UTC, datetime


def pin_checksum(*, account_id: str, board_id: str | None, title: str, destination_url: str) -> str:
    """Deterministic identity of a pin intent (idempotency + dedupe)."""
    payload = json.dumps(
        {
            "account_id": account_id,
            "board_id": board_id or "",
            "title": title.strip().lower(),
            "destination_url": destination_url,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def is_valid_queue_transition(current: str, target: str) -> bool:
    """Queue state machine (blueprint §5.4)."""
    transitions = {
        "queued": {"claimed", "cancelled"},
        "claimed": {"done", "failed", "cancelled"},
        "done": set(),
        "failed": {"queued"},  # retry resets to queued for the next attempt
        "cancelled": set(),
    }
    return target in transitions.get(current, set())


def is_valid_pin_transition(current: str, target: str) -> bool:
    """Pin ledger state machine (blueprint §5.4)."""
    transitions = {
        "draft": {"queued", "cancelled"},
        "queued": {"publishing", "cancelled"},
        "publishing": {"published", "failed"},
        "published": {"deleted"},
        "failed": {"queued", "cancelled"},
        "deleted": set(),
        "cancelled": set(),
    }
    return target in transitions.get(current, set())


def attempt_status_for_error(*, retryable: bool, attempts: int, max_attempts: int) -> str:
    """Derive the attempt status from the error kind and attempt count.

    Retryable failures below the cap are recorded as ``retryable`` and the
    queue item is reset to ``queued`` for a later run; permanent failures
    and exhausted retries are ``failed``.
    """
    if retryable and attempts < max_attempts:
        return "retryable"
    return "failed"


def utc_now() -> datetime:
    return datetime.now(UTC)
