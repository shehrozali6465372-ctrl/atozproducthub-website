"""Executor unit tests (M10 Step 2): sibling HTTP calls, tenancy, errors.

Each executor is exercised against a mocked sibling transport — no real
services are contacted. The assertions verify the frozen API surface
(paths, auth header, X-Niche-Id forwarding) and the success/failure
result contract.
"""

import asyncio
import json

import httpx

from atoz_automation_service.executors import (
    AffiliateReconciliationExecutor,
    AiosDispatchExecutor,
    AnalyticsRollupExecutor,
    ExecutorContext,
    PinterestExecutor,
    SeoSitemapExecutor,
    build_default_registry,
)

from .fixtures import make_settings


def build_context(executor, *, niche_id="n-1", payload=None, settings=None, transport=None):
    """Construct an ExecutorContext with a mocked sibling transport."""
    from atoz_automation_service.executors.clients import SiblingClients

    siblings = SiblingClients(settings or make_settings(), transport=transport)
    return (
        ExecutorContext(
            executor_name=executor.name,
            queue_item_id="q-1",
            job_run_id="r-1",
            scheduled_job_id="j-1",
            niche_id=niche_id,
            payload=payload or {},
            settings=settings or make_settings(),
            siblings=siblings,
        ),
        siblings,
    )


def scenario(runner):
    return asyncio.run(runner())


def test_registry_registers_builtins_and_rejects_empty_name() -> None:
    registry = build_default_registry()
    names = registry.names()
    assert names == [
        "affiliate.reconciliation",
        "aios.dispatch",
        "analytics.rollup",
        "pinterest.publish_due",
        "seo.sitemap_rebuild",
    ]

    class Nameless:
        name = ""
        queue = "x"

        async def execute(self, ctx):
            return None

    try:
        registry.register(Nameless())  # type: ignore[arg-type]
        raise AssertionError("expected ValueError for empty executor name")
    except ValueError:
        pass


def test_pinterest_executor_success_and_tenancy() -> None:
    async def run() -> None:
        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["niche"] = request.headers.get("X-Niche-Id")
            captured["auth"] = bool(request.headers.get("Authorization", "").startswith("Bearer "))
            return httpx.Response(
                200,
                json=[
                    {"pin_id": "p1", "status": "published"},
                    {"pin_id": "p2", "status": "failed"},
                ],
            )

        executor = PinterestExecutor()
        ctx, siblings = build_context(
            executor, payload={"limit": 5}, transport=httpx.MockTransport(handler)
        )
        try:
            result = await executor.execute(ctx)
            assert result.status == "success"
            assert "pins published: 1" in result.summary
            assert captured["niche"] == "n-1"
            assert captured["auth"] is True
            assert "/api/v1/admin/queue/publish-due" in captured["url"]
            assert "niche_id=n-1" in captured["url"]
        finally:
            await siblings.aclose()

    scenario(run)


def test_pinterest_executor_all_failed_is_retryable() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[{"pin_id": "p1", "status": "failed"}])

        executor = PinterestExecutor()
        ctx, siblings = build_context(executor, transport=httpx.MockTransport(handler))
        try:
            result = await executor.execute(ctx)
            assert result.status == "failed"
            assert result.retryable is True
        finally:
            await siblings.aclose()

    scenario(run)


def test_pinterest_executor_sibling_error_is_retryable() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"detail": "busy"})

        executor = PinterestExecutor()
        ctx, siblings = build_context(executor, transport=httpx.MockTransport(handler))
        try:
            result = await executor.execute(ctx)
            assert result.status == "failed"
            assert result.retryable is True
            assert "pinterest-service:" in result.error
        finally:
            await siblings.aclose()

    scenario(run)


def test_seo_executor_requires_niche() -> None:
    async def run() -> None:
        executor = SeoSitemapExecutor()
        ctx, siblings = build_context(executor, niche_id=None)
        try:
            result = await executor.execute(ctx)
            assert result.status == "failed"
            assert result.retryable is False
        finally:
            await siblings.aclose()

    scenario(run)


def test_seo_executor_success() -> None:
    async def run() -> None:
        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["path"] = request.url.path
            return httpx.Response(200, json={"shard_count": 3, "shards": ["s1", "s2", "s3"]})

        executor = SeoSitemapExecutor()
        ctx, siblings = build_context(
            executor, payload={"group": "articles"}, transport=httpx.MockTransport(handler)
        )
        try:
            result = await executor.execute(ctx)
            assert result.status == "success"
            assert result.metadata["shard_count"] == 3
            assert captured["path"] == "/api/v1/admin/sitemaps/articles/rebuild"
        finally:
            await siblings.aclose()

    scenario(run)


def test_affiliate_executor_success() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json={"id": "rec-1", "delta_cents": 125})

        executor = AffiliateReconciliationExecutor()
        ctx, siblings = build_context(
            executor,
            payload={
                "network_id": "net-1",
                "reported_at": "2026-08-13",
                "expected_total_cents": 1000,
                "actual_total_cents": 1125,
                "report_ref": "ref-1",
            },
            transport=httpx.MockTransport(handler),
        )
        try:
            result = await executor.execute(ctx)
            assert result.status == "success"
            assert result.output_ref == "rec-1"
            assert result.metadata["delta_cents"] == 125
        finally:
            await siblings.aclose()

    scenario(run)


def test_affiliate_executor_validation_failure() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, json={"detail": "network not found"})

        executor = AffiliateReconciliationExecutor()
        ctx, siblings = build_context(
            executor, payload={"network_id": "bad"}, transport=httpx.MockTransport(handler)
        )
        try:
            result = await executor.execute(ctx)
            assert result.status == "failed"
            assert result.retryable is True
        finally:
            await siblings.aclose()

    scenario(run)


def test_analytics_executor_success() -> None:
    async def run() -> None:
        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(200, json=[{}, {}, {}])

        executor = AnalyticsRollupExecutor()
        ctx, siblings = build_context(
            executor,
            payload={"from_date": "2026-08-13", "to_date": "2026-08-13"},
            transport=httpx.MockTransport(handler),
        )
        try:
            result = await executor.execute(ctx)
            assert result.status == "success"
            assert result.metadata["days"] == 3
            assert "/api/v1/admin/rollups" in captured["url"]
        finally:
            await siblings.aclose()

    scenario(run)


def test_analytics_executor_requires_niche() -> None:
    async def run() -> None:
        executor = AnalyticsRollupExecutor()
        ctx, siblings = build_context(executor, niche_id=None)
        try:
            result = await executor.execute(ctx)
            assert result.status == "failed"
            assert result.retryable is False
        finally:
            await siblings.aclose()

    scenario(run)


def test_aios_executor_dispatch_success() -> None:
    async def run() -> None:
        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["path"] = request.url.path
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"job_id": "aios-job-1"})

        executor = AiosDispatchExecutor()
        ctx, siblings = build_context(
            executor,
            payload={
                "job_id": "a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
                "contract": "content-intake",
                "request": {"article_id": "art-1"},
            },
            transport=httpx.MockTransport(handler),
        )
        try:
            result = await executor.execute(ctx)
            assert result.status == "success"
            assert result.output_ref == "aios-job-1"
            assert captured["path"] == "/bridge/jobs"
            assert captured["body"]["niche_id"] == "n-1"
            assert captured["body"]["contract"] == "content-intake"
        finally:
            await siblings.aclose()

    scenario(run)


def test_aios_executor_internal_token_header() -> None:
    async def run() -> None:
        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["token"] = request.headers.get("X-Bridge-Token")
            return httpx.Response(200, json={"job_id": "aios-job-1"})

        settings = make_settings(aios_bridge_internal_token="shared-token-123")
        executor = AiosDispatchExecutor()
        ctx, siblings = build_context(
            executor,
            payload={
                "job_id": "a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
                "contract": "seo-metadata",
                "request": {"article_id": "art-1"},
            },
            settings=settings,
            transport=httpx.MockTransport(handler),
        )
        try:
            result = await executor.execute(ctx)
            assert result.status == "success"
            assert captured["token"] == "shared-token-123"
        finally:
            await siblings.aclose()

    scenario(run)


def test_aios_executor_missing_contract_is_non_retryable() -> None:
    async def run() -> None:
        executor = AiosDispatchExecutor()
        ctx, siblings = build_context(executor, payload={"job_id": "j-1"})
        try:
            result = await executor.execute(ctx)
            assert result.status == "failed"
            assert result.retryable is False
        finally:
            await siblings.aclose()

    scenario(run)


def test_aios_executor_bridge_unavailable_is_retryable() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"detail": "AI OS busy"})

        executor = AiosDispatchExecutor()
        ctx, siblings = build_context(
            executor,
            payload={
                "job_id": "a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
                "contract": "analytics-insights",
                "request": {},
            },
            transport=httpx.MockTransport(handler),
        )
        try:
            result = await executor.execute(ctx)
            assert result.status == "failed"
            assert result.retryable is True
        finally:
            await siblings.aclose()

    scenario(run)
