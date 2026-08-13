"""RBAC hardening tests (Task 19 §1).

Covers the frozen permission catalog + system-role matrix, operator
identity CRUD, niche-scoped role assignment/revocation, effective
permission resolution, and the MFA-verified gate for privileged actions.
"""

from atoz_admin_service.uuids import uuid7

from .fixtures import (
    TEST_WRITE_PERMISSIONS,
    access_token,
    api_client,
    build_app,
    headers,
    make_settings,
    scenario,
)

READ_TOKEN = access_token(permissions=("admin:read",))
WRITE_TOKEN = access_token(permissions=TEST_WRITE_PERMISSIONS)
NICHE_A = uuid7()
NICHE_B = uuid7()


def test_permission_catalog_and_system_roles_are_seeded() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            perms = (
                await client.get("/api/v1/admin/permissions", headers=headers(token=READ_TOKEN))
            ).json()
            codes = {p["code"] for p in perms}
            assert {
                "content:read",
                "affiliate:write",
                "pinterest:write",
                "seo:read",
                "analytics:write",
                "admin:read",
                "admin:write",
                "automation:read",
            } <= codes

            roles = (
                await client.get("/api/v1/admin/roles", headers=headers(token=READ_TOKEN))
            ).json()
            role_codes = {r["code"] for r in roles}
            assert {
                "super_admin",
                "admin",
                "editor",
                "viewer",
                "pinterest_operator",
                "finance",
            } <= role_codes
            by_code = {r["code"]: r for r in roles}
            assert "admin:write" in by_code["super_admin"]["permissions"]
            assert "content:write" in by_code["editor"]["permissions"]
            assert "admin:write" not in by_code["viewer"]["permissions"]

    scenario(run)


def test_rbac_denies_missing_permissions() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            viewer = access_token(permissions=("content:read",))
            response = await client.get("/api/v1/admin/roles", headers=headers(token=viewer))
            assert response.status_code == 403
            assert response.json()["code"] == "FORBIDDEN"

    scenario(run)


def test_unauthenticated_requests_are_rejected() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            response = await client.get("/api/v1/admin/roles")
            assert response.status_code == 401
            assert response.json()["code"] == "UNAUTHENTICATED"

    scenario(run)


def test_user_crud_and_role_assignment() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            created = await client.post(
                "/api/v1/admin/users",
                headers=headers(token=WRITE_TOKEN),
                json={
                    "subject": "op-1",
                    "email": "op-1@example.com",
                    "display_name": "Operator One",
                    "status": "active",
                    "roles": [{"role_code": "editor", "niche_id": NICHE_A}],
                },
            )
            assert created.status_code == 201, created.text
            user = created.json()
            assert user["email"] == "op-1@example.com"
            assert len(user["roles"]) == 1
            assert user["roles"][0]["role_code"] == "editor"
            assert user["roles"][0]["niche_id"] == NICHE_A

            # Duplicate subject rejected.
            duplicate = await client.post(
                "/api/v1/admin/users",
                headers=headers(token=WRITE_TOKEN),
                json={
                    "subject": "op-1",
                    "email": "other@example.com",
                    "display_name": "Dup",
                    "status": "active",
                    "roles": [],
                },
            )
            assert duplicate.status_code == 409
            assert duplicate.json()["code"] == "DUPLICATE"

            # Assign a niche-scoped role, then revoke it.
            assigned = await client.post(
                f"/api/v1/admin/users/{user['id']}/roles",
                headers=headers(token=WRITE_TOKEN),
                json={"role_code": "viewer", "niche_id": NICHE_B},
            )
            assert assigned.status_code == 201
            detail = (
                await client.get(
                    f"/api/v1/admin/users/{user['id']}", headers=headers(token=READ_TOKEN)
                )
            ).json()
            assert {r["role_code"] for r in detail["roles"]} == {"editor", "viewer"}

            revoked = await client.post(
                f"/api/v1/admin/users/{user['id']}/roles/revoke",
                headers=headers(token=WRITE_TOKEN),
                json={"role_code": "viewer", "niche_id": NICHE_B},
            )
            assert revoked.status_code == 200
            detail = (
                await client.get(
                    f"/api/v1/admin/users/{user['id']}", headers=headers(token=READ_TOKEN)
                )
            ).json()
            assert [r["role_code"] for r in detail["roles"]] == ["editor"]

    scenario(run)


def test_mfa_gate_blocks_privileged_actions() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        app.state.session_manager = _SessionManagerForTest()
        async with await api_client(app) as client:
            response = await client.post(
                "/api/v1/admin/users",
                headers=headers(token=WRITE_TOKEN),
                json={
                    "subject": "op-mfa",
                    "email": "op-mfa@example.com",
                    "display_name": "MFA Operator",
                    "status": "active",
                    "roles": [],
                },
            )
            assert response.status_code == 403
            assert response.json()["code"] == "MFA_REQUIRED"

    scenario(run)


def test_effective_permissions_resolve_across_roles() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        service = app.state.admin_service
        created = await service.create_user(
            subject="multi-role",
            email="multi@example.com",
            display_name="Multi Role",
            status="active",
            roles=[
                {"role_code": "editor", "niche_id": NICHE_A},
                {"role_code": "finance", "niche_id": NICHE_A},
            ],
        )
        perms = await service.effective_permissions("multi-role")
        assert "content:write" in perms
        assert "affiliate:write" in perms
        assert "analytics:read" in perms
        assert "admin:write" not in perms
        assert created is not None

    scenario(run)


def test_mfa_provision_endpoint() -> None:
    async def run() -> None:
        app, _engine = await build_app()
        async with await api_client(app) as client:
            response = await client.post(
                "/api/v1/admin/mfa/provision", headers=headers(token=READ_TOKEN)
            )
            assert response.status_code == 200
            body = response.json()
            assert body["subject"] == "tester"
            assert body["otpauth_uri"].startswith("otpauth://totp/")

    scenario(run)


class _SessionManagerForTest:
    """Session manager whose sessions are never MFA-verified."""

    async def get(self, session_id: str):
        return None

    async def revoke(self, session_id: str) -> None:
        return None


def test_startup_seed_is_resilient_when_schema_is_missing() -> None:
    """Compose starts the control plane before migrations run (ADR-0009 §4).

    Seeding reference data must not crash startup when the admin tables do
    not exist yet; the readiness probe reports DB health independently.
    """

    async def run() -> None:
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import StaticPool

        from atoz_admin_service.main import create_app

        engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        app = create_app(settings=make_settings(), session_factory=session_factory)
        async with app.router.lifespan_context(app):
            pass  # startup must not raise when the schema is absent
        await engine.dispose()

    scenario(run)
