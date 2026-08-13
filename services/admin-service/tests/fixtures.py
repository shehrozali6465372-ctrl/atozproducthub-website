"""Shared helpers for admin-service tests.

Builds an in-memory SQLite app (same pattern as the analytics service):
API tests run through httpx ASGITransport inside ``asyncio.run`` and never
cross event-loop boundaries. Tables are created from the metadata, and the
frozen RBAC catalog is seeded idempotently.
"""

import hashlib
import hmac
import json
from collections.abc import Callable, Coroutine
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from atoz_admin_service.config import Settings
from atoz_admin_service.main import create_app
from atoz_backend_core.auth import create_access_token
from atoz_backend_core.db.base import Base

TEST_JWT_SECRET = "test-admin-jwt-secret-0123456789abcdef0123456789abcdef"
TEST_EVENT_SECRET = "test-admin-event-secret-0123456789abcdef0123456789abcdef"
TEST_READ_PERMISSIONS = ("admin:read",)
TEST_WRITE_PERMISSIONS = ("admin:read", "admin:write")


def make_settings(**overrides: object) -> Settings:
    """Test settings: fixed secrets, no rate limiting."""
    base: dict[str, object] = {
        "app_env": "test",
        "rate_limit_enabled": False,
        "jwt_secret": TEST_JWT_SECRET,
        "event_webhook_secret": TEST_EVENT_SECRET,
        "audit_export_max_rows": 100,
        "audit_default_page_size": 50,
    }
    base.update(overrides)
    return Settings(**base)


def access_token(
    *,
    subject: str = "tester",
    permissions: tuple[str, ...] = TEST_WRITE_PERMISSIONS,
    secret: str = TEST_JWT_SECRET,
) -> str:
    """Mint a JWT access token for admin API tests (RBAC claims)."""
    return create_access_token(
        secret=secret,
        subject=subject,
        session_id="test-session",
        permissions=permissions,
    )


def event_signature(secret: str, payload: dict[str, Any]) -> str:
    """HMAC-SHA256 over the canonical JSON payload (raw-body convention)."""
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


class VerifiedSessionManager:
    """Session manager whose ``test-session`` is MFA-verified.

    Lets write-path tests exercise the MFA gate without TOTP (the
    Authentication milestone owns real TOTP verification).
    """

    async def get(self, session_id: str):
        from atoz_backend_core.auth.sessions import Session

        return Session(
            session_id=session_id,
            subject="tester",
            permissions=("admin:read", "admin:write"),
            mfa_verified=True,
        )

    async def revoke(self, session_id: str) -> None:
        return None


async def build_app(
    *,
    settings: Settings | None = None,
    seed: bool = True,
    mfa_verified: bool = True,
) -> tuple[FastAPI, AsyncEngine]:
    """Create an app with a fresh in-memory database and seeded RBAC.

    ``mfa_verified=False`` swaps in a manager whose sessions are never
    verified so the MFA gate can be tested.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app = create_app(settings=settings or make_settings(), session_factory=session_factory)
    if mfa_verified:
        app.state.session_manager = VerifiedSessionManager()
    if seed:
        await app.state.admin_service.seed_reference_data()
    return app, engine


async def api_client(app: FastAPI) -> httpx.AsyncClient:
    """Async test client for the given app (same event loop)."""
    from httpx import ASGITransport, AsyncClient

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def scenario(runner: Callable[[], Coroutine[Any, Any, None]]) -> None:
    """Run an async scenario helper through the event loop (no pytest-asyncio)."""
    import asyncio

    asyncio.run(runner())


def headers(*, token: str | None = None, niche: str | None = None) -> dict[str, str]:
    """Build auth + tenancy headers for admin API calls."""
    result: dict[str, str] = {}
    if token:
        result["Authorization"] = f"Bearer {token}"
    if niche:
        result["X-Niche-Id"] = niche
    return result
