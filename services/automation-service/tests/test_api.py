"""Automation admin API tests: RBAC, tenancy header, idempotent trigger."""

import httpx

from .fixtures import access_token, build_app, scenario

_NO_TOKEN = object()


def httpx_client(app, *, token=_NO_TOKEN, permissions=None):
    """Async client with the given auth token (default: write permissions)."""
    if token is _NO_TOKEN:
        token = access_token(
            permissions=tuple(permissions)
            if permissions
            else ("automation:read", "automation:write")
        )
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver", headers=headers
    )


def test_api_requires_authentication() -> None:
    async def run():
        app, _, _, _ = await build_app()
        async with httpx_client(app, token=None) as client:
            response = await client.get("/api/v1/admin/rules")
            assert response.status_code == 401

    scenario(run)


def test_api_requires_permission() -> None:
    async def run():
        app, _, _, _ = await build_app()
        async with httpx_client(app, permissions=("analytics:read",)) as client:
            response = await client.get("/api/v1/admin/rules")
            assert response.status_code == 403

    scenario(run)


def test_api_create_enable_trigger_flow() -> None:
    async def run():
        app, _, _, _ = await build_app()
        async with httpx_client(app) as client:
            create = await client.post(
                "/api/v1/admin/rules",
                json={"code": "api-rule", "trigger_type": "manual", "config": {"step": 1}},
            )
            assert create.status_code == 201
            rule = create.json()
            assert rule["status"] == "disabled"

            enable = await client.post(f"/api/v1/admin/rules/{rule['id']}/enable")
            assert enable.status_code == 200
            assert enable.json()["status"] == "enabled"

            first = await client.post(
                f"/api/v1/admin/rules/{rule['id']}/trigger",
                headers={"Idempotency-Key": "api-key-1"},
            )
            assert first.status_code == 200
            assert first.json()["created"] is True

            replay = await client.post(
                f"/api/v1/admin/rules/{rule['id']}/trigger",
                headers={"Idempotency-Key": "api-key-1"},
            )
            assert replay.status_code == 200
            assert replay.json()["created"] is False
            assert replay.json()["run"]["id"] == first.json()["run"]["id"]

            runs = await client.get("/api/v1/admin/runs")
            assert runs.status_code == 200
            assert len(runs.json()) == 1

    scenario(run)


def test_api_tenancy_header_isolates_queries() -> None:
    async def run():
        from atoz_automation_service.services import AutomationService
        from atoz_automation_service.uuids import uuid7

        app, _, _, _ = await build_app()
        service: AutomationService = app.state.automation_service
        niche_a = await service.create_niche(name="A", slug="api-a", status="active")
        await service.create_rule(niche_id=niche_a.id, code="scoped-rule", trigger_type="manual")

        async with httpx_client(app) as client:
            # Global scope sees no niche rows.
            response = await client.get("/api/v1/admin/rules")
            assert response.status_code == 200
            assert response.json() == []

            # Niche scope sees only its rows.
            scoped = await client.get("/api/v1/admin/rules", headers={"X-Niche-Id": niche_a.id})
            assert scoped.status_code == 200
            assert [r["code"] for r in scoped.json()] == ["scoped-rule"]

            # Unregistered niche is rejected.
            unknown = await client.get("/api/v1/admin/rules", headers={"X-Niche-Id": str(uuid7())})
            assert unknown.status_code == 422

            # Malformed UUID is rejected.
            bad = await client.get("/api/v1/admin/rules", headers={"X-Niche-Id": "not-a-uuid"})
            assert bad.status_code == 422

    scenario(run)


def test_api_aios_jobs_require_niche() -> None:
    async def run():
        app, _, _, _ = await build_app()
        async with httpx_client(app) as client:
            response = await client.post(
                "/api/v1/admin/aios-jobs",
                json={"job_id": "j1", "contract": "AIOS.Content.Intake"},
            )
            assert response.status_code == 422

    scenario(run)
