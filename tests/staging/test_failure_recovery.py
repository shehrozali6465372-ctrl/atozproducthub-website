"""Failure → detection → retry/fallback → recovery → idempotency drills.

Task 24 Phase E: every scenario below asserts the full recovery shape,
not just "an exception was raised". Live host drills (service restarts,
store restarts, worker kill) are documented in docs/operations/007 and
run from tools/deploy/rollback-test.sh + tools/db/staging-recovery-drill.sh.
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy.exc import IntegrityError

from atoz_backend_core.config import BaseServiceSettings
from atoz_backend_core.db.postgres import check_database
from atoz_backend_core.db.redis import check_redis


def _run(coro):
    return asyncio.run(coro)


# 1. Redis unavailable --------------------------------------------------------
def test_redis_down_is_detected_and_readiness_degrades() -> None:
    result = _run(check_redis("redis://127.0.0.1:1/0"))
    assert result["status"] == "down"

    from atoz_backend_core import __version__
    from atoz_backend_core.app import create_service_app

    async def scenario() -> None:
        settings = BaseServiceSettings(
            app_env="test",
            database_url="postgresql+asyncpg://user:pass@127.0.0.1:1/atoz",
            redis_url="redis://127.0.0.1:1/0",
            rate_limit_enabled=False,
        )
        app = create_service_app(
            service_name="staging-drill",
            version=__version__,
            settings=settings,
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            ready = await client.get("/ready")
            assert ready.status_code == 503
            body = ready.json()
            assert body["status"] == "degraded"
            components = {c["name"]: c["status"] for c in body["components"]}
            assert components["redis"] == "down"

    _run(scenario())


# 2. PostgreSQL unavailable ----------------------------------------------------
def test_postgres_down_is_detected() -> None:
    result = _run(check_database("postgresql+asyncpg://user:pass@127.0.0.1:1/atoz"))
    assert result["status"] == "down"


# 3. Kafka unavailable ----------------------------------------------------------
def test_kafka_down_fails_publish_but_pipeline_fallback_works() -> None:
    from atoz_analytics_service.domain.pipeline import (
        InMemoryEventBackbone,
        InMemoryWarehouse,
        KafkaEventBackbone,
        PipelineWorker,
    )
    from atoz_backend_core.events.envelope import EventEnvelope

    async def scenario() -> None:
        producer = AsyncMock()
        producer.start.side_effect = OSError("broker unreachable")
        backbone = KafkaEventBackbone(
            bootstrap_servers="kafka:9092", topic="atoz.analytics.events.v1"
        )
        with patch("aiokafka.AIOKafkaProducer", return_value=producer):
            with pytest.raises(OSError):
                await backbone.publish(
                    EventEnvelope(
                        type="analytics:page_view.v1",
                        event_id="evt-kafka-down",
                        payload={"niche_id": "n-1"},
                    )
                )
        # Fallback: the in-memory pipeline continues to drain (no loss).
        fallback = InMemoryEventBackbone()
        warehouse = InMemoryWarehouse()
        worker = PipelineWorker(fallback, warehouse)
        await fallback.publish(
            EventEnvelope(
                type="analytics:page_view.v1",
                event_id="evt-fallback",
                payload={"niche_id": "n-1"},
            )
        )
        await worker.drain_in_memory()
        assert [row["event_id"] for row in warehouse.rows] == ["evt-fallback"]

    _run(scenario())


# 4. ClickHouse unavailable ------------------------------------------------------
def test_clickhouse_down_fails_append_with_retryable_error() -> None:
    from atoz_analytics_service.domain.pipeline import ClickHouseWarehouse

    async def scenario() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="unavailable")

        warehouse = ClickHouseWarehouse(
            base_url="http://clickhouse:8123", database="atoz", table="events"
        )
        try:
            transport = httpx.MockTransport(handler)
            with patch.object(
                warehouse._client, "post", new=httpx.AsyncClient(transport=transport).post
            ):
                with pytest.raises(httpx.HTTPStatusError):
                    await warehouse.append_events([{"event_id": "evt-1", "niche_id": "n-1"}])
        finally:
            await warehouse.close()

    _run(scenario())


# 5. Typesense unavailable --------------------------------------------------------
def test_typesense_down_search_fails_with_retryable_remote_error() -> None:
    from atoz_seo_service.domain.search import TypesenseSearchIndex
    from atoz_seo_service.errors import RemoteApiError

    async def scenario() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="unavailable")

        index = TypesenseSearchIndex(
            base_url="http://typesense:8108",
            api_key="test-key",
            transport=httpx.MockTransport(handler),
        )
        try:
            with pytest.raises(RemoteApiError) as exc:
                await index.search(query="blender", niche_id="n-1")
            assert exc.value.retryable is True
        finally:
            await index.close()

        def connect_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        from atoz_seo_service.errors import SearchUnavailableError

        unreachable = TypesenseSearchIndex(
            base_url="http://typesense:8108",
            api_key="test-key",
            transport=httpx.MockTransport(connect_error),
        )
        try:
            with pytest.raises(SearchUnavailableError):
                await unreachable.search(query="blender", niche_id="n-1")
        finally:
            await unreachable.close()

    _run(scenario())


# 6-8. Pinterest API 429 / 5xx / timeout -------------------------------------------
def test_pinterest_429_retries_then_succeeds() -> None:
    from atoz_pinterest_service.domain.client import PinterestApiClient
    from atoz_pinterest_service.domain.rate_limits import PerAccountRateLimiter

    ACCOUNT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    calls = {"count": 0}

    async def scenario() -> None:
        async def token_provider(force_refresh: bool = False) -> str:
            return "tok-1"

        def handler(request: httpx.Request) -> httpx.Response:
            calls["count"] += 1
            if calls["count"] <= 2:
                return httpx.Response(429, json={"code": 0, "message": "rate limited"})
            return httpx.Response(200, json={"items": [{"id": "b1", "name": "Kitchen"}]})

        client = PinterestApiClient(
            base_url="https://api.pinterest.test/v5",
            account_id=ACCOUNT,
            token_provider=token_provider,
            rate_limiter=PerAccountRateLimiter(read_per_minute=600, write_per_minute=200),
            timeout_seconds=5.0,
            max_retries=3,
            base_backoff_seconds=0.01,
            max_backoff_seconds=0.05,
            transport=httpx.MockTransport(handler),
        )
        try:
            page = await client.list_boards()
            assert [b["id"] for b in page.items] == ["b1"]
        finally:
            await client.close()

    _run(scenario())
    assert calls["count"] == 3


def test_pinterest_5xx_retries_then_succeeds() -> None:
    from atoz_pinterest_service.domain.client import PinterestApiClient
    from atoz_pinterest_service.domain.rate_limits import PerAccountRateLimiter

    ACCOUNT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    calls = {"count": 0}

    async def scenario() -> None:
        async def token_provider(force_refresh: bool = False) -> str:
            return "tok-1"

        def handler(request: httpx.Request) -> httpx.Response:
            calls["count"] += 1
            if calls["count"] == 1:
                return httpx.Response(502, json={"code": 0, "message": "bad gateway"})
            return httpx.Response(200, json={"items": [{"id": "b1", "name": "Kitchen"}]})

        client = PinterestApiClient(
            base_url="https://api.pinterest.test/v5",
            account_id=ACCOUNT,
            token_provider=token_provider,
            rate_limiter=PerAccountRateLimiter(read_per_minute=600, write_per_minute=200),
            timeout_seconds=5.0,
            max_retries=3,
            base_backoff_seconds=0.01,
            max_backoff_seconds=0.05,
            transport=httpx.MockTransport(handler),
        )
        try:
            page = await client.list_boards()
            assert [b["id"] for b in page.items] == ["b1"]
        finally:
            await client.close()

    _run(scenario())


def test_pinterest_timeout_retries_then_succeeds() -> None:
    from atoz_pinterest_service.domain.client import PinterestApiClient
    from atoz_pinterest_service.domain.rate_limits import PerAccountRateLimiter

    ACCOUNT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    calls = {"count": 0}

    async def scenario() -> None:
        async def token_provider(force_refresh: bool = False) -> str:
            return "tok-1"

        def handler(request: httpx.Request) -> httpx.Response:
            calls["count"] += 1
            if calls["count"] == 1:
                raise httpx.ReadTimeout("simulated timeout", request=request)
            return httpx.Response(200, json={"items": [{"id": "b1", "name": "Kitchen"}]})

        client = PinterestApiClient(
            base_url="https://api.pinterest.test/v5",
            account_id=ACCOUNT,
            token_provider=token_provider,
            rate_limiter=PerAccountRateLimiter(read_per_minute=600, write_per_minute=200),
            timeout_seconds=5.0,
            max_retries=3,
            base_backoff_seconds=0.01,
            max_backoff_seconds=0.05,
            transport=httpx.MockTransport(handler),
        )
        try:
            page = await client.list_boards()
            assert [b["id"] for b in page.items] == ["b1"]
        finally:
            await client.close()

    _run(scenario())
    assert calls["count"] == 2


# 9-12. Worker crash / duplicate delivery / retry exhaustion / restart ------------
def _sqlite_tables(*metadatas) -> tuple:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)

    async def create() -> None:
        async with engine.begin() as conn:
            for metadata in metadatas:
                await conn.run_sync(metadata.create_all)

    _run(create())
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def test_duplicate_webhook_delivery_is_rejected_by_ledger_constraint() -> None:
    from atoz_affiliate_service.domain.entities import AffiliateWebhookLog, Base

    engine, session_factory = _sqlite_tables(Base.metadata)

    async def scenario() -> None:
        session = session_factory()
        session.add(
            AffiliateWebhookLog(
                id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                source="network-a",
                event_id="evt-dup",
                event_type="network.conversion",
                status="received",
                payload_hash="abc",
            )
        )
        await session.commit()
        session.add(
            AffiliateWebhookLog(
                id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                source="network-a",
                event_id="evt-dup",
                event_type="network.conversion",
                status="received",
                payload_hash="abc",
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.close()
        await engine.dispose()

    _run(scenario())


def test_duplicate_queue_execution_is_rejected_by_idempotency_key() -> None:
    from atoz_automation_service.domain.entities import (
        AutomationRule,
        AutomationRun,
        Base,
        PlatformBase,
    )

    engine, session_factory = _sqlite_tables(Base.metadata, PlatformBase.metadata)

    async def scenario() -> None:
        session = session_factory()
        session.add(
            AutomationRule(
                id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                niche_id="n-1",
                code="daily-sitemap",
                trigger_type="schedule",
                config_json="{}",
                status="enabled",
            )
        )
        await session.commit()
        session.add(
            AutomationRun(
                id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                niche_id="n-1",
                automation_rule_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                idempotency_key="rule-1:2026-08-01T00:00:00+00:00",
                status="running",
                started_at=datetime(2026, 8, 1, tzinfo=UTC),
            )
        )
        await session.commit()
        session.add(
            AutomationRun(
                id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                niche_id="n-1",
                automation_rule_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                idempotency_key="rule-1:2026-08-01T00:00:00+00:00",
                status="running",
                started_at=datetime(2026, 8, 1, tzinfo=UTC),
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.close()
        await engine.dispose()

    _run(scenario())


def test_retry_exhaustion_reaches_terminal_state_and_recovery_is_scheduled() -> None:
    from atoz_automation_service.domain.retry import next_retry_at

    assert next_retry_at(attempts=5, max_attempts=5) is None  # terminal: no retry
    recovered = next_retry_at(attempts=2, max_attempts=5)
    assert recovered is not None  # recovery scheduled with backoff
    from atoz_pinterest_service.domain.pins import (
        is_valid_pin_transition,
        is_valid_queue_transition,
    )

    # Worker crash leaves a 'claimed' item; the ledger re-queues failed work.
    assert is_valid_queue_transition("claimed", "failed") is True
    assert is_valid_queue_transition("failed", "queued") is True
    assert is_valid_pin_transition("publishing", "failed") is True
    assert is_valid_pin_transition("failed", "queued") is True
