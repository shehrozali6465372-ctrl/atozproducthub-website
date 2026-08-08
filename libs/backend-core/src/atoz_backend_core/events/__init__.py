"""Domain event system: envelope, bus, publisher, subscriber.

Infrastructure only — the event types themselves are registered by services
(Phase 4+). M3 ships the mechanism plus in-memory and Redis transports; no
business events exist yet (API Contracts §9: ``*.v1`` naming, dedupe by
``event_id``).
"""

from atoz_backend_core.events.bus import EventBus, InMemoryEventBus, RedisEventBus
from atoz_backend_core.events.envelope import EventEnvelope, event_id_from, new_event_id
from atoz_backend_core.events.publisher import EventPublisher

__all__ = [
    "EventBus",
    "EventEnvelope",
    "EventPublisher",
    "InMemoryEventBus",
    "RedisEventBus",
    "event_id_from",
    "new_event_id",
]
