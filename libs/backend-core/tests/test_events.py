"""Event envelope + in-memory bus tests (API Contracts §9)."""

import asyncio

import pytest

from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.envelope import EventEnvelope, event_id_from, new_event_id
from atoz_backend_core.events.publisher import EventPublisher


def test_envelope_type_validation() -> None:
    EventEnvelope(type="niches.created.v1", event_id=new_event_id()).validate_type()
    with pytest.raises(ValueError):
        EventEnvelope(type="niches.created", event_id=new_event_id()).validate_type()


def test_event_id_from_is_deterministic() -> None:
    assert event_id_from("seed") == event_id_from("seed")
    assert event_id_from("seed") != event_id_from("other")


def test_in_memory_bus_dispatch() -> None:
    async def scenario() -> None:
        bus = InMemoryEventBus()
        received: list[EventEnvelope] = []

        async def handler(event: EventEnvelope) -> None:
            received.append(event)

        await bus.subscribe("niches.created.v1", handler)
        await bus.publish(
            EventEnvelope(
                type="niches.created.v1",
                event_id=new_event_id(),
                payload={"niche_id": "n1"},
                aggregate_id="n1",
            )
        )
        assert len(received) == 1
        assert received[0].aggregate_id == "n1"

    asyncio.run(scenario())


def test_publisher_facade() -> None:
    async def scenario() -> None:
        bus = InMemoryEventBus()
        publisher = EventPublisher(bus, publisher="content-service")
        await publisher.publish(
            EventEnvelope(type="articles.published.v1", event_id=new_event_id())
        )
        assert publisher.name == "content-service"

    asyncio.run(scenario())
