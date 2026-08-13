"""Audit ledger tests (Task 19 §4).

The audit ledger is append-only: records are written once, never updated,
never deleted. Search is filterable by actor/action/entity/niche/request ID,
and exports are capped by the export-control setting.
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
NICHE = uuid7()


def test_audit_records_are_append_only() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        await service.record_audit(
            action="create",
            entity_type="article",
            entity_id="art-1",
            niche_id=NICHE,
            admin_user_id="tester",
            after_json='{"title": "v1"}',
        )
        await service.record_audit(
            action="update",
            entity_type="article",
            entity_id="art-1",
            niche_id=NICHE,
            admin_user_id="tester",
            after_json='{"title": "v2"}',
        )
        async with await api_client(app) as client:
            rows = (
                await client.get(
                    "/api/v1/admin/audit", headers=headers(token=READ_TOKEN, niche=NICHE)
                )
            ).json()
            assert len(rows) == 2
            assert {r["action"] for r in rows} == {"create", "update"}
            assert all(r["niche_id"] == NICHE for r in rows)
            assert all(r["admin_user_id"] == "tester" for r in rows)

            # Search by entity + action.
            filtered = (
                await client.get(
                    "/api/v1/admin/audit?entity_type=article&entity_id=art-1&action=update",
                    headers=headers(token=READ_TOKEN),
                )
            ).json()
            assert len(filtered) == 1
            assert filtered[0]["after_json"] == '{"title": "v2"}'

            # No update/delete API surface exists for audit records.
            updated = await client.patch(
                "/api/v1/admin/audit/art-1", headers=headers(token=WRITE_TOKEN), json={}
            )
            assert updated.status_code in (404, 405)
            deleted = await client.delete(
                "/api/v1/admin/audit/art-1", headers=headers(token=WRITE_TOKEN)
            )
            assert deleted.status_code in (404, 405)

    scenario(run)


def test_audit_export_is_capped_and_csv() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        for index in range(25):
            await service.record_audit(
                action="export",
                entity_type="niche",
                entity_id=f"n-{index}",
                admin_user_id="tester",
            )
        async with await api_client(app) as client:
            response = await client.get(
                "/api/v1/admin/audit/export", headers=headers(token=READ_TOKEN)
            )
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/csv")
            assert "Content-Disposition" in response.headers
            lines = response.text.strip().splitlines()
            assert lines[0].startswith("id,occurred_at,admin_user_id")
            # Header + at most export-max rows.
            assert len(lines) <= 26

    scenario(run)


def test_audit_requires_admin_read_permission() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            token = access_token(permissions=("analytics:read",))
            response = await client.get("/api/v1/admin/audit", headers=headers(token=token))
            assert response.status_code == 403

    scenario(run)
