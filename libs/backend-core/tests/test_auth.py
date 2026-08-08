"""Auth primitives: password hashing, JWT, RBAC, sessions, MFA provision."""

import asyncio
import time

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from atoz_backend_core.auth import (
    InMemorySessionManager,
    MfaService,
    Role,
    RoleRegistry,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    require_permissions,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("s3cret!")
    assert hashed != "s3cret!"
    assert verify_password("s3cret!", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_access_and_refresh() -> None:
    access = create_access_token(
        secret="test-secret-0123456789abcdef0123456789abcdef",
        subject="user-1",
        session_id="sess-1",
        permissions=("articles:read", "articles:write"),
    )
    claims = decode_token(
        access,
        secret="test-secret-0123456789abcdef0123456789abcdef",
        expected_type="access",
    )
    assert claims.subject == "user-1"
    assert claims.session_id == "sess-1"
    assert claims.permissions == ("articles:read", "articles:write")
    assert claims.expires_at > int(time.time())

    refresh = create_refresh_token(
        secret="test-secret-0123456789abcdef0123456789abcdef",
        subject="user-1",
        session_id="sess-1",
    )
    claims = decode_token(
        refresh,
        secret="test-secret-0123456789abcdef0123456789abcdef",
        expected_type="refresh",
    )
    assert claims.token_type == "refresh"


def test_jwt_wrong_type_rejected() -> None:
    refresh = create_refresh_token(
        secret="test-secret-0123456789abcdef0123456789abcdef",
        subject="user-1",
        session_id="sess-1",
    )
    with pytest.raises(jwt.PyJWTError):
        decode_token(
            refresh,
            secret="test-secret-0123456789abcdef0123456789abcdef",
            expected_type="access",
        )


def test_role_registry_permissions() -> None:
    registry = RoleRegistry()
    registry.register(Role(name="admin", permissions=frozenset({"*"})))
    registry.register(
        Role(name="editor", permissions=frozenset({"articles:read", "articles:write"}))
    )
    assert registry.permissions_for(["editor"]) == frozenset({"articles:read", "articles:write"})
    assert "*" in registry.permissions_for(["admin"])


def test_require_permissions_dependency() -> None:
    app = FastAPI()

    @app.get("/protected")
    def protected(
        _: object = Depends(require_permissions("articles:read")),
    ) -> dict[str, str]:
        return {"ok": "true"}

    with TestClient(app) as core_client:
        assert core_client.get("/protected").status_code == 401  # no auth context


def test_in_memory_session_lifecycle() -> None:
    async def scenario() -> None:
        manager = InMemorySessionManager()
        session = await manager.create(
            subject="user-1",
            permissions=("articles:read",),
            ttl_seconds=60,
        )
        assert await manager.get(session.session_id) is not None
        assert (await manager.get(session.session_id)).permissions == ("articles:read",)
        await manager.revoke(session.session_id)
        assert await manager.get(session.session_id) is None

    asyncio.run(scenario())


def test_in_memory_session_expiry() -> None:
    async def scenario() -> None:
        manager = InMemorySessionManager()
        session = await manager.create(subject="user-1", ttl_seconds=-1)
        assert await manager.get(session.session_id) is None

    asyncio.run(scenario())


def test_mfa_provisioning() -> None:
    service = MfaService(issuer="AtozProductHub")
    provision = service.provision("admin@atoz.dev")
    assert provision.otpauth_uri.startswith("otpauth://totp/")
    assert provision.secret
    with pytest.raises(NotImplementedError):
        service.verify("admin@atoz.dev", provision.secret, "123456")
