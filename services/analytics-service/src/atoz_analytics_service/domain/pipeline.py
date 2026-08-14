"""Event backbone + analytical warehouse abstractions (Task 18 §3).

Pipeline: PostgreSQL operational ledger -> Kafka event backbone ->
ClickHouse analytical warehouse (Database Blueprint §5.16, §11). The ABCs
keep the service testable without brokers — the in-memory implementations
are the dev/CI default and the Kafka/ClickHouse clients are the production
transport. No analytics intelligence lives here; this is pure plumbing.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

import httpx

from atoz_backend_core.events.envelope import EventEnvelope

logger = logging.getLogger("atoz.analytics.pipeline")


# ---------------------------------------------------------------- backbone
class EventBackbone(ABC):
    """Publishes analytics event envelopes to the pipeline."""

    @abstractmethod
    async def publish(self, envelope: EventEnvelope) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...


class InMemoryEventBackbone(EventBackbone):
    """Dev/test backbone: keeps envelopes in memory for pipeline assertions."""

    def __init__(self) -> None:
        self.published: list[EventEnvelope] = []

    async def publish(self, envelope: EventEnvelope) -> None:
        self.published.append(envelope)

    async def close(self) -> None:
        self.published.clear()


class KafkaEventBackbone(EventBackbone):
    """Production backbone: Kafka producer with lazy connect + flush.

    Uses the ``atoz.analytics.events.v1`` topic; each envelope is published
    as a JSON document so any consumer (ClickHouse writer, automation) can
    replay the stream. Connection is lazy so service health never depends on
    the broker being reachable.
    """

    def __init__(
        self,
        *,
        bootstrap_servers: str,
        topic: str,
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str = "PLAIN",
        sasl_username: str = "",
        sasl_password: str = "",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._security_protocol = security_protocol
        self._sasl_mechanism = sasl_mechanism
        self._sasl_username = sasl_username
        self._sasl_password = sasl_password
        self._producer: Any | None = None

    async def _ensure_producer(self) -> Any:
        if self._producer is None:
            from aiokafka import AIOKafkaProducer

            kwargs: dict[str, object] = {
                "bootstrap_servers": self._bootstrap_servers,
                "security_protocol": self._security_protocol,
            }
            if self._sasl_username and self._sasl_password:
                kwargs.update(
                    {
                        "sasl_mechanism": self._sasl_mechanism,
                        "sasl_plain_username": self._sasl_username,
                        "sasl_plain_password": self._sasl_password,
                    }
                )
            self._producer = AIOKafkaProducer(**kwargs)
            await self._producer.start()
        return self._producer

    async def publish(self, envelope: EventEnvelope) -> None:
        producer = await self._ensure_producer()
        message = {
            "type": envelope.type,
            "event_id": envelope.event_id,
            "payload": envelope.payload,
            "aggregate_id": envelope.aggregate_id,
            "occurred_at": envelope.occurred_at,
        }
        await producer.send_and_wait(self._topic, json.dumps(message).encode())

    async def close(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None


# --------------------------------------------------------------- warehouse
class Warehouse(ABC):
    """Append-only analytical storage (ClickHouse in production)."""

    @abstractmethod
    async def append_events(self, rows: Sequence[dict[str, Any]]) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...


class InMemoryWarehouse(Warehouse):
    """Dev/test warehouse: rows kept in memory for pipeline assertions."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    async def append_events(self, rows: Sequence[dict[str, Any]]) -> None:
        self.rows.extend(rows)

    async def close(self) -> None:
        self.rows.clear()


class ClickHouseWarehouse(Warehouse):
    """Production warehouse: ClickHouse HTTP interface (JSONEachRow)."""

    def __init__(self, *, base_url: str, database: str, table: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._database = database
        self._table = table
        self._client = httpx.AsyncClient(timeout=10.0)

    def _insert_query(self) -> str:
        return f"INSERT INTO {self._database}.{self._table} FORMAT JSONEachRow"

    async def append_events(self, rows: Sequence[dict[str, Any]]) -> None:
        if not rows:
            return
        body = "\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n"
        response = await self._client.post(
            self._base_url + "/",
            params={"query": self._insert_query()},
            content=body,
        )
        response.raise_for_status()

    async def close(self) -> None:
        await self._client.aclose()


# ------------------------------------------------------------ pipeline run
class PipelineWorker:
    """Drains a backbone into a warehouse.

    In tests the in-memory backbone/warehouse prove the end-to-end path
    (collector -> ledger -> backbone -> warehouse). In production a Kafka
    consumer loop calls the same ``process_envelope`` conversion so the
    warehouse schema stays identical regardless of transport.
    """

    def __init__(self, backbone: EventBackbone, warehouse: Warehouse) -> None:
        self._backbone = backbone
        self._warehouse = warehouse

    async def drain_in_memory(self) -> None:
        """Flush an in-memory backbone into the warehouse (test/dev path)."""
        if isinstance(self._backbone, InMemoryEventBackbone):
            rows = [event_row(envelope) for envelope in self._backbone.published]
            self._backbone.published.clear()
            await self._warehouse.append_events(rows)


def event_row(envelope: EventEnvelope) -> dict[str, Any]:
    """Convert an envelope to a warehouse row (denormalized context)."""
    payload = envelope.payload or {}
    return {
        "event_id": envelope.event_id,
        "niche_id": payload.get("niche_id", ""),
        "pinterest_account_id": payload.get("pinterest_account_id"),
        "pinterest_pin_id": payload.get("pinterest_pin_id") or payload.get("pin_id"),
        "event_type": envelope.type,
        "page_url": payload.get("page_url", ""),
        "referrer": payload.get("referrer", ""),
        "session_id": payload.get("session_id", ""),
        "user_pseudo_id": payload.get("user_pseudo_id", ""),
        "traits_json": json.dumps(payload.get("traits", {}), separators=(",", ":")),
        "occurred_at": payload.get("occurred_at", ""),
        "received_at": payload.get("received_at", ""),
    }
