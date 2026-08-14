"""Pipeline tests: backbone publish, warehouse append, and transport mocks."""

from unittest.mock import AsyncMock, patch

from atoz_analytics_service.domain.pipeline import (
    ClickHouseWarehouse,
    InMemoryEventBackbone,
    InMemoryWarehouse,
    KafkaEventBackbone,
    PipelineWorker,
    event_row,
)
from atoz_backend_core.events.envelope import EventEnvelope

from .fixtures import scenario


def test_event_row_maps_envelope_to_warehouse_row() -> None:
    envelope = EventEnvelope(
        type="analytics:page_view.v1",
        event_id="evt-0001",
        payload={
            "niche_id": "niche-1",
            "pinterest_account_id": "acct-1",
            "event_type": "page_view",
            "page_url": "/articles/a",
            "referrer": "",
            "session_id": "s1",
            "user_pseudo_id": "u1",
            "traits": {"device": "mobile"},
            "occurred_at": "2026-08-01T10:00:00+00:00",
            "received_at": "2026-08-01T10:00:01+00:00",
        },
        aggregate_id="evt-0001",
    )
    row = event_row(envelope)
    assert row["event_id"] == "evt-0001"
    assert row["niche_id"] == "niche-1"
    assert row["pinterest_account_id"] == "acct-1"
    assert row["traits_json"] == '{"device":"mobile"}'


def test_pipeline_worker_drains_backbone_into_warehouse() -> None:
    async def runner() -> None:
        backbone = InMemoryEventBackbone()
        warehouse = InMemoryWarehouse()
        worker = PipelineWorker(backbone, warehouse)
        await backbone.publish(
            EventEnvelope(
                type="analytics:page_view.v1", event_id="evt-0001", payload={"niche_id": "n1"}
            )
        )
        await backbone.publish(
            EventEnvelope(
                type="analytics:page_view.v1", event_id="evt-0002", payload={"niche_id": "n1"}
            )
        )
        assert len(warehouse.rows) == 0
        await worker.drain_in_memory()
        assert len(warehouse.rows) == 2
        assert warehouse.rows[0]["event_id"] == "evt-0001"
        assert len(backbone.published) == 0

    scenario(runner)


def test_kafka_backbone_publishes_json_message() -> None:
    async def runner() -> None:
        producer = AsyncMock()
        backbone = KafkaEventBackbone(
            bootstrap_servers="kafka:9092", topic="atoz.analytics.events.v1"
        )
        with patch("aiokafka.AIOKafkaProducer", return_value=producer) as factory:
            await backbone.publish(
                EventEnvelope(
                    type="analytics:page_view.v1", event_id="evt-0001", payload={"niche_id": "n1"}
                )
            )
            factory.assert_called_once_with(
                bootstrap_servers="kafka:9092", security_protocol="PLAINTEXT"
            )
            producer.send_and_wait.assert_awaited_once()
            topic, message = producer.send_and_wait.call_args.args
            assert topic == "atoz.analytics.events.v1"
            assert b'"event_id": "evt-0001"' in message
            await backbone.close()
            producer.stop.assert_awaited_once()

    scenario(runner)


def test_kafka_backbone_passes_sasl_credentials() -> None:
    """Phase C: SASL_PLAINTEXT credentials reach the producer when set."""

    async def runner() -> None:
        producer = AsyncMock()
        backbone = KafkaEventBackbone(
            bootstrap_servers="kafka:9092",
            topic="atoz.analytics.events.v1",
            security_protocol="SASL_PLAINTEXT",
            sasl_mechanism="PLAIN",
            sasl_username="atoz",
            sasl_password="s3cret",
        )
        with patch("aiokafka.AIOKafkaProducer", return_value=producer) as factory:
            await backbone.publish(
                EventEnvelope(
                    type="analytics:page_view.v1", event_id="evt-0002", payload={"niche_id": "n1"}
                )
            )
            factory.assert_called_once_with(
                bootstrap_servers="kafka:9092",
                security_protocol="SASL_PLAINTEXT",
                sasl_mechanism="PLAIN",
                sasl_plain_username="atoz",
                sasl_plain_password="s3cret",
            )
            await backbone.close()

    scenario(runner)


def test_clickhouse_warehouse_posts_json_each_row() -> None:
    async def runner() -> None:
        client = AsyncMock()
        client.post.return_value.raise_for_status = lambda: None
        warehouse = ClickHouseWarehouse(
            base_url="http://clickhouse:8123", database="atoz_analytics", table="analytics_events"
        )
        warehouse._client = client
        await warehouse.append_events([{"event_id": "evt-0001", "niche_id": "n1"}])
        client.post.assert_awaited_once()
        _, kwargs = client.post.call_args
        assert kwargs["params"] == {
            "query": "INSERT INTO atoz_analytics.analytics_events FORMAT JSONEachRow"
        }
        assert kwargs["content"] == '{"event_id":"evt-0001","niche_id":"n1"}\n'
        await warehouse.close()

    scenario(runner)
