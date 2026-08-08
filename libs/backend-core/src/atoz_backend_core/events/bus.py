"""Event bus: publish/subscribe with in-memory and Redis transports.

The Redis transport uses pub/sub with the ``atez.events.<type>`` channel so
services can fan out domain events without a broker; a durable broker
(Redis Streams/Kafka) is a later swap behind the same bus protocol.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

import redis.asyncio as aioredis

from atoz_backend_core.events.envelope import EventEnvelope

Handler = Callable[[EventEnvelope], Awaitable[None]]


class EventBus(Protocol):
    """Publish and subscribe contract for domain events."""

    async def publish(self, event: EventEnvelope) -> None: ...

    async def subscribe(self, event_type: str, handler: Handler) -> None: ...


class InMemoryEventBus:
    """Async in-memory bus: handlers run sequentially per event."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    async def publish(self, event: EventEnvelope) -> None:
        event.validate_type()
        for handler in list(self._handlers.get(event.type, ())):
            await handler(event)

    async def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)


class RedisEventBus:
    """Redis pub/sub transport; subscribers must be started explicitly."""

    def __init__(self, redis_url: str) -> None:
        self._client = aioredis.from_url(redis_url, decode_responses=True)
        self._handlers: dict[str, list[Handler]] = {}
        self._listener_task: asyncio.Task | None = None

    async def publish(self, event: EventEnvelope) -> None:
        event.validate_type()
        import json

        await self._client.publish(f"atoz.events.{event.type}", json.dumps(event.__dict__))

    async def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def start_listener(self) -> None:
        """Start consuming the subscribed channels (idempotent)."""
        if self._listener_task is not None:
            return
        pubsub = self._client.pubsub()

        async def _listen() -> None:
            import json

            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                channel = str(message.get("channel", ""))
                event_type = channel.removeprefix("atoz.events.")
                try:
                    data = json.loads(message["data"])
                except (TypeError, ValueError):
                    continue
                event = EventEnvelope(
                    type=str(data.get("type", event_type)),
                    event_id=str(data.get("event_id", "")),
                    payload=data.get("payload") or {},
                    aggregate_id=data.get("aggregate_id"),
                    occurred_at=float(data.get("occurred_at") or 0.0),
                )
                for handler in list(self._handlers.get(event.type, ())):
                    await handler(event)

        for event_type in self._handlers:
            await pubsub.subscribe(f"atoz.events.{event_type}")
        self._listener_task = asyncio.create_task(_listen())

    async def close(self) -> None:
        if self._listener_task is not None:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None
        await self._client.aclose()
