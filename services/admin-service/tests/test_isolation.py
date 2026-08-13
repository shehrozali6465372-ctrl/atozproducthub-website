"""Tenancy/isolation tests for the admin control plane (Task 19 §1, §5).

The admin service must never leak one niche's records into another:
scoped reads are filtered server-side by ``X-Niche-Id`` and cross-niche
queries return only the requested scope.
"""

from atoz_admin_service.uuids import uuid7

from .fixtures import (
    access_token,
    api_client,
    build_app,
    headers,
    scenario,
)

READ_TOKEN = access_token(permissions=("admin:read",))
WRITE_TOKEN = access_token(permissions=("admin:read", "admin:write"))
NICHE_A = uuid7()
NICHE_B = uuid7()


def test_audit_queries_are_niche_scoped() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        await service.record_audit(
            action="publish",
            entity_type="article",
            entity_id="a-1",
            niche_id=NICHE_A,
            admin_user_id="tester",
        )
        await service.record_audit(
            action="publish",
            entity_type="article",
            entity_id="b-1",
            niche_id=NICHE_B,
            admin_user_id="tester",
        )
        async with await api_client(app) as client:
            scope_a = (
                await client.get(
                    "/api/v1/admin/audit", headers=headers(token=READ_TOKEN, niche=NICHE_A)
                )
            ).json()
            assert len(scope_a) == 1
            assert scope_a[0]["entity_id"] == "a-1"

            scope_b = (
                await client.get(
                    "/api/v1/admin/audit", headers=headers(token=READ_TOKEN, niche=NICHE_B)
                )
            ).json()
            assert len(scope_b) == 1
            assert scope_b[0]["entity_id"] == "b-1"

            # Unscoped query returns everything (global admin view).
            all_rows = (
                await client.get("/api/v1/admin/audit", headers=headers(token=READ_TOKEN))
            ).json()
            assert {r["entity_id"] for r in all_rows} == {"a-1", "b-1"}

    scenario(run)


def test_queue_visibility_is_niche_scoped() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        await service.enqueue(
            niche_id=NICHE_A, queue="pins", payload_ref="pin-a", run_at=None, max_attempts=5
        )
        await service.enqueue(
            niche_id=NICHE_B, queue="pins", payload_ref="pin-b", run_at=None, max_attempts=5
        )
        await service.enqueue(
            niche_id=None, queue="default", payload_ref="global-job", run_at=None, max_attempts=5
        )
        async with await api_client(app) as client:
            scope_a = (
                await client.get(
                    "/api/v1/admin/queue", headers=headers(token=READ_TOKEN, niche=NICHE_A)
                )
            ).json()
            assert {item["payload_ref"] for item in scope_a} == {"pin-a"}

            scope_b = (
                await client.get(
                    "/api/v1/admin/queue", headers=headers(token=READ_TOKEN, niche=NICHE_B)
                )
            ).json()
            assert {item["payload_ref"] for item in scope_b} == {"pin-b"}

            all_items = (
                await client.get("/api/v1/admin/queue", headers=headers(token=READ_TOKEN))
            ).json()
            assert {item["payload_ref"] for item in all_items} == {"pin-a", "pin-b", "global-job"}

    scenario(run)


def test_niche_scope_is_required_to_be_a_valid_uuid() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            response = await client.get(
                "/api/v1/admin/audit", headers=headers(token=READ_TOKEN, niche="not-a-uuid")
            )
            assert response.status_code == 422
            assert response.json()["code"] == "VALIDATION_FAILED"

    scenario(run)
