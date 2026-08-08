"""Event publisher: thin facade over a bus with payload/type guards.

Services construct events as ``EventEnvelope`` objects and publish them
through this facade; no business logic lives here.
"""

from collections.abc import Awaitable, Callable

from atoz_backend_core.events.bus import EventBus
from atoz_backend_core.events.envelope import EventEnvelope


class EventPublisher:
    """Typed publish facade: validates the envelope before publishing."""

    def __init__(self, bus: EventBus, *, publisher: str) -> None:
        self._bus = bus
        self._publisher = publisher

    async def publish(self, event: EventEnvelope) -> None:
        event.validate_type()
        await self._bus.publish(event)

    @property
    def name(self) -> str:
        return self._publisher

    # Expose subscribe for tests/manual wiring; services normally register
    # handlers at startup.
    async def subscribe(
        self, event_type: str, handler: Callable[[EventEnvelope], Awaitable[None]]
    ) -> None:
        await self._bus.subscribe(event_type, handler)
