"""Operations dashboard + operational tools tests (Task 19 §2, §3, §5).

Covers queue visibility + safe retry, webhook/operation log search, job
visibility, sibling-service probes, and the niche isolation verification.
"""

from atoz_admin_service.uuids import uuid7

from .fixtures import (
    access_token,
    api_client,
    build_app,
    headers,
    make_settings,
    scenario,
)

READ_TOKEN = access_token(permissions=("admin:read",))
WRITE_TOKEN = access_token(permissions=("admin:read", "admin:write"))
NICHE = uuid7()


def test_ops_overview_reports_failures_and_queues() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        await service.enqueue(
            niche_id=NICHE,
            queue="pins",
            payload_ref="pin-1",
            run_at=None,
            max_attempts=5,
        )
        await service.record_operation(
            operation="pinterest.pin_publish",
            entity_type="pin",
            entity_id="pin-1",
            niche_id=NICHE,
            status="failed",
            message="pinterest 429",
        )
        async with await api_client(app) as client:
            response = await client.get(
                "/api/v1/admin/ops/overview", headers=headers(token=READ_TOKEN)
            )
            assert response.status_code == 200
            body = response.json()
            assert body["failed_operations"] == 1
            assert body["failed_queue_items"] == 0
            assert body["queues"]["queued"] == 1
            assert body["audit_entries"] >= 1

    scenario(run)


def test_system_status_reports_ok_without_probes() -> None:
    async def run() -> None:
        app, _engine = await build_app(settings=make_settings(service_health_urls={}))
        async with await api_client(app) as client:
            response = await client.get(
                "/api/v1/admin/ops/status", headers=headers(token=READ_TOKEN)
            )
            assert response.status_code == 200
            body = response.json()
            assert body["overall"] == "ok"
            assert body["services"][0]["name"] == "admin-service"
            assert body["services"][0]["status"] == "ok"

    scenario(run)


def test_system_status_probes_sibling_services() -> None:
    async def run() -> None:
        settings = make_settings(
            service_health_urls={"content-service": "http://unreachable-host:8200"}
        )
        app, _engine = await build_app(settings=settings)
        async with await api_client(app) as client:
            response = await client.get(
                "/api/v1/admin/ops/status", headers=headers(token=READ_TOKEN)
            )
            assert response.status_code == 200
            body = response.json()
            probe = next(s for s in body["services"] if s["name"] == "content-service")
            assert probe["status"] == "down"
            assert probe["error"] is not None

    scenario(run)


def test_queue_retry_only_applies_to_failed_items() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        queued = await service.enqueue(
            niche_id=NICHE, queue="pins", payload_ref="pin-1", run_at=None, max_attempts=5
        )
        async with await api_client(app) as client:
            # Queued items cannot be retried.
            response = await client.post(
                f"/api/v1/admin/queue/{queued.id}/retry", headers=headers(token=WRITE_TOKEN)
            )
            assert response.status_code == 422

            # Force a failure through the repository, then retry succeeds.
            async with service._uow_factory().transaction() as uow:
                item = await uow.queue.get(queued.id)
                item.state = "failed"
                item.attempts = 1
                await uow.commit()
            response = await client.post(
                f"/api/v1/admin/queue/{queued.id}/retry", headers=headers(token=WRITE_TOKEN)
            )
            assert response.status_code == 200
            body = response.json()
            assert body["state"] == "queued"
            assert body["error"] is None

    scenario(run)


def test_webhook_and_operation_logs_are_searchable() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        await service.record_operation(
            operation="affiliate.click",
            entity_type="link",
            entity_id="l-1",
            niche_id=NICHE,
            status="succeeded",
            message="click recorded",
        )
        await service.record_operation(
            operation="seo.sitemap_rebuilt",
            entity_type="sitemap",
            entity_id="s-1",
            status="failed",
            message="xml invalid",
        )
        async with await api_client(app) as client:
            failed = (
                await client.get(
                    "/api/v1/admin/logs/operations?status=failed", headers=headers(token=READ_TOKEN)
                )
            ).json()
            assert len(failed) == 1
            assert failed[0]["operation"] == "seo.sitemap_rebuilt"

            scoped = (
                await client.get(
                    "/api/v1/admin/logs/operations", headers=headers(token=READ_TOKEN, niche=NICHE)
                )
            ).json()
            assert len(scoped) == 1
            assert scoped[0]["operation"] == "affiliate.click"

            webhooks = (
                await client.get("/api/v1/admin/logs/webhooks", headers=headers(token=READ_TOKEN))
            ).json()
            assert webhooks == []

    scenario(run)


def test_isolation_check_reports_clean_tenancy() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        await service.create_niche(name="Niche A", slug="niche-a", status="active")
        await service.enqueue(
            niche_id=NICHE, queue="pins", payload_ref="pin-1", run_at=None, max_attempts=5
        )
        async with await api_client(app) as client:
            response = await client.get(
                "/api/v1/admin/ops/isolation", headers=headers(token=READ_TOKEN)
            )
            assert response.status_code == 200
            body = response.json()
            # NICHE is not registered locally -> its scoped rows are orphans.
            assert body["ok"] is False
            orphan_tables = {c["table"] for c in body["checks"] if c["orphaned"]}
            assert "queue" in orphan_tables

    scenario(run)
