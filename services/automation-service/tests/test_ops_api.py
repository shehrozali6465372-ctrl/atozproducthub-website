"""Automation ops API tests (M10 Step 2): executors, jobs/runs, queue controls."""

from .fixtures import build_app, scenario
from .test_api import httpx_client


def test_api_lists_executors_with_read_permission() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        async with httpx_client(app) as client:
            response = await client.get("/api/v1/admin/executors")
            assert response.status_code == 200
            names = {e["name"] for e in response.json()}
            assert names == {
                "pinterest.publish_due",
                "seo.sitemap_rebuild",
                "affiliate.reconciliation",
                "analytics.rollup",
                "aios.dispatch",
            }

    scenario(run)


def test_api_executors_require_auth() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        async with httpx_client(app, token=None) as client:
            response = await client.get("/api/v1/admin/executors")
            assert response.status_code == 401

    scenario(run)


def test_api_enqueue_job_with_config() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        service = app.state.automation_service
        niche = await service.create_niche(name="A", slug="ops-a", status="active")
        job = await service.create_scheduled_job(
            niche_id=niche.id,
            job_key="ops-job",
            cron_expr="0 6 * * *",
            queue="seo",
            handler="seo.sitemap_rebuild",
            config={"group": "articles"},
        )
        async with httpx_client(app) as client:
            response = await client.post(
                f"/api/v1/admin/scheduled-jobs/{job.id}/enqueue",
                json={"config": {"group": "products"}},
                headers={"X-Niche-Id": niche.id},
            )
            assert response.status_code == 201
            body = response.json()
            assert body["run"]["status"] == "pending"
            assert body["queue_item"]["state"] == "queued"

            # The scheduled job definition stays frozen.
            stored = await service.get_scheduled_job(job.id, niche.id)
            assert "products" not in stored.config_json

    scenario(run)


def test_api_job_runs_detailed_includes_key_and_slug() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        service = app.state.automation_service
        niche = await service.create_niche(name="Niche A", slug="ops-niche", status="active")
        job = await service.create_scheduled_job(
            niche_id=niche.id,
            job_key="ops-run-job",
            cron_expr="0 6 * * *",
            queue="seo",
            handler="seo.sitemap_rebuild",
        )
        await service.enqueue_job(job.id, niche.id)
        async with httpx_client(app) as client:
            response = await client.get("/api/v1/admin/jobs/runs", headers={"X-Niche-Id": niche.id})
            assert response.status_code == 200
            rows = response.json()
            assert rows[0]["job_key"] == "ops-run-job"
            assert rows[0]["niche_slug"] == "ops-niche"

    scenario(run)


def test_api_queue_detailed_includes_niche_slug() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        service = app.state.automation_service
        niche = await service.create_niche(name="Niche B", slug="ops-queue", status="active")
        item, _created = await service.enqueue(
            niche_id=niche.id, queue="seo", payload_ref="job_run:x"
        )
        async with httpx_client(app) as client:
            response = await client.get(
                "/api/v1/admin/queue/detailed", headers={"X-Niche-Id": niche.id}
            )
            assert response.status_code == 200
            rows = response.json()
            assert rows[0]["id"] == item.id
            assert rows[0]["niche_slug"] == "ops-queue"

    scenario(run)


def test_api_retry_queue_item_and_cancel() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        service = app.state.automation_service
        niche = await service.create_niche(name="Niche C", slug="ops-retry", status="active")
        item, _created = await service.enqueue(
            niche_id=niche.id, queue="seo", payload_ref="job_run:failed-1"
        )
        await service.claim_queue_item(item.id, niche.id)
        await service.fail_queue_item(item.id, niche.id, error="boom", retry=False)

        async with httpx_client(app) as client:
            retried = await client.post(
                f"/api/v1/admin/queue/{item.id}/retry", headers={"X-Niche-Id": niche.id}
            )
            assert retried.status_code == 200
            assert retried.json()["state"] == "queued"

            cancelled = await client.post(
                f"/api/v1/admin/queue/{item.id}/cancel", headers={"X-Niche-Id": niche.id}
            )
            # queued items are cancellable; the item is now failed by operator.
            assert cancelled.status_code == 200
            assert cancelled.json()["state"] == "failed"
            assert cancelled.json()["error"] == "cancelled by operator"

    scenario(run)


def test_api_retry_job_run_creates_fresh_execution() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        service = app.state.automation_service
        niche = await service.create_niche(name="Niche D", slug="ops-run", status="active")
        job = await service.create_scheduled_job(
            niche_id=niche.id,
            job_key="ops-retry-run",
            cron_expr="0 6 * * *",
            queue="seo",
            handler="seo.sitemap_rebuild",
        )
        run_row, _item = await service.enqueue_job(job.id, niche.id)
        await service.start_job_run(run_row.id, niche.id)
        failed = await service.fail_job_run(run_row.id, niche.id, error="boom", retry=False)
        assert failed.status == "failed"

        async with httpx_client(app) as client:
            response = await client.post(
                f"/api/v1/admin/job-runs/{run_row.id}/retry",
                headers={"X-Niche-Id": niche.id},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["run"]["id"] != run_row.id
            assert body["run"]["status"] == "pending"

    scenario(run)


def test_api_cancel_queue_item_rejects_terminal() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        service = app.state.automation_service
        item, _created = await service.enqueue(
            niche_id=None, queue="seo", payload_ref="job_run:done-1"
        )
        await service.claim_queue_item(item.id, None)
        await service.complete_queue_item(item.id, None)
        async with httpx_client(app) as client:
            response = await client.post(f"/api/v1/admin/queue/{item.id}/cancel")
            assert response.status_code == 422

    scenario(run)


def test_api_queue_controls_are_niche_isolated() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        service = app.state.automation_service
        niche_a = await service.create_niche(name="A", slug="ops-iso-a", status="active")
        niche_b = await service.create_niche(name="B", slug="ops-iso-b", status="active")
        item_a, _created = await service.enqueue(
            niche_id=niche_a.id, queue="seo", payload_ref="job_run:iso-a"
        )
        async with httpx_client(app) as client:
            # Cross-niche retry resolves as not-found (no leakage).
            response = await client.post(
                f"/api/v1/admin/queue/{item_a.id}/retry", headers={"X-Niche-Id": niche_b.id}
            )
            assert response.status_code == 404
            # Own niche works.
            response = await client.post(
                f"/api/v1/admin/queue/{item_a.id}/cancel", headers={"X-Niche-Id": niche_a.id}
            )
            assert response.status_code == 200

    scenario(run)


def test_api_retry_run_requires_write_permission() -> None:
    async def run() -> None:
        app, _, _, _ = await build_app()
        async with httpx_client(app, permissions=("automation:read",)) as client:
            response = await client.post("/api/v1/admin/job-runs/any/retry")
            assert response.status_code == 403

    scenario(run)
