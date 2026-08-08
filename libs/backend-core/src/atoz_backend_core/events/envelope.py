"""Event envelope: ``type.v1`` namespacing and ``event_id`` dedupe.

Conforms to API Contracts §9: every internal event carries a versioned type
(e.g. ``niches.created.v1``), a unique event id, and an optional aggregate
reference for correlation. Handlers use ``event_id`` for idempotency.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def new_event_id() -> str:
    return uuid.uuid4().hex


def event_id_from(seed: str) -> str:
    """Deterministic event id from a seed (used for idempotent re-emits)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


@dataclass(frozen=True)
class EventEnvelope:
    type: str  # e.g. "niches.created.v1"
    event_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    aggregate_id: str | None = None
    occurred_at: float = field(default_factory=time.time)

    def validate_type(self) -> None:
        """Validate the ``name.vN`` convention; raises ValueError otherwise."""
        name, sep, version = self.type.rpartition(".")
        if not sep or not name or not version.startswith("v") or not version[1:].isdigit():
            raise ValueError(f"event type must be '<name>.v<N>', got {self.type!r}")
