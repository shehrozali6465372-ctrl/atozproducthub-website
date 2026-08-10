"""Shared helpers for pinterest-service tests.

Builds an in-memory SQLite app inside the caller's event loop (backend-core
test pattern): API tests run through httpx ASGITransport inside
``asyncio.run`` and never cross event-loop boundaries. Token material lives
in an InMemoryTokenVault; the Pinterest API client is pointed at a mock
transport.
"""

import json
from collections.abc import Callable, Coroutine
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from atoz_backend_core.auth import create_access_token
from atoz_backend_core.db.base import Base
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher
from atoz_pinterest_service.config import Settings
from atoz_pinterest_service.domain.secrets import InMemoryTokenVault
from atoz_pinterest_service.main import create_app
from atoz_pinterest_service.services import PinterestService

TEST_JWT_SECRET = "test-pinterest-jwt-secret-0123456789abcdef0123456789abcdef"
TEST_OAUTH_STATE_SECRET = "test-pinterest-oauth-state-secret-0123456789abcdef0123456789abcdef"
TEST_READ_PERMISSIONS = ("pinterest:read",)
TEST_WRITE_PERMISSIONS = ("pinterest:read", "pinterest:write")


def make_settings(**overrides: object) -> Settings:
    """Test settings: no rate limits, fixed secrets, local OAuth config."""
    base: dict[str, object] = {
        "app_env": "test",
        "rate_limit_enabled": False,
        "jwt_secret": TEST_JWT_SECRET,
        "oauth_state_secret": TEST_OAUTH_STATE_SECRET,
        "oauth_client_id": "test-client-id",
        "oauth_client_secret_ref": "test:test-client-secret",
        "oauth_redirect_uri": "http://test/oauth/callback",
        "pinterest_api_base": "https://api.pinterest.test/v5",
        "rate_limit_read_per_minute": 600,
        "rate_limit_write_per_minute": 200,
        "max_retries": 2,
        "base_backoff_seconds": 0.01,
        "max_backoff_seconds": 0.05,
        "public_base_url": "https://atozproducthub.dev",
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


class MockPinterestTransport(httpx.MockTransport):
    """Configurable Pinterest API mock (boards/pins/token endpoints)."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.boards: list[dict[str, Any]] = []
        self.pins: list[dict[str, Any]] = []
        self.fail_with: list[tuple[int, str]] = []
        self._fail_index = 0
        self.token_exchange_payload: dict[str, Any] | None = None
        self.token_exchange_status: int = 200
        super().__init__(self._handler)

    def add_failure(self, status_code: int, body: str = "") -> None:
        self.fail_with.append((status_code, body))

    async def _handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        url = str(request.url)
        # OAuth token endpoint (form-encoded POST to the token URL).
        if url.startswith("https://api.pinterest.test/v5/oauth/token") or "oauth/token" in url:
            if self.token_exchange_status >= 400:
                return httpx.Response(self.token_exchange_status, json={"error": "invalid_grant"})
            payload = self.token_exchange_payload or {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_in": 3600,
                "scope": "boards:read boards:write pins:read pins:write",
            }
            return httpx.Response(200, json=payload)
        if self.fail_with:
            status, body = self.fail_with.pop(0)
            headers = {"retry-after": "1"} if status == 429 else {}
            return httpx.Response(status, text=body, headers=headers)

        if request.method == "GET" and url.endswith("/user_account"):
            return httpx.Response(200, json={"username": "mock-user", "id": "u-1"})
        if request.method == "GET" and "/boards" in url and "/sections" not in url:
            return httpx.Response(200, json={"items": self.boards, "bookmark": None})
        if request.method == "POST" and url.endswith("/boards"):
            body = json.loads(request.content)
            board = {
                "id": f"b-{len(self.boards) + 1}",
                "name": body["name"],
                "description": body.get("description", ""),
            }
            self.boards.append(board)
            return httpx.Response(201, json=board)
        if request.method == "GET" and url.endswith("/pins"):
            return httpx.Response(200, json={"items": self.pins, "bookmark": None})
        if request.method == "POST" and url.endswith("/pins"):
            body = json.loads(request.content)
            pin = {
                "id": f"p-{len(self.pins) + 1}",
                "link": "https://www.pinterest.com/pin/p-1/",
                "board_id": body.get("board_id"),
            }
            self.pins.append(pin)
            return httpx.Response(201, json=pin)
        if request.method == "GET" and "/pins/" in url:
            pin_id = url.rstrip("/").rsplit("/", 1)[-1]
            found_pin: dict[str, Any] | None = next(
                (p for p in self.pins if p["id"] == pin_id), None
            )
            if found_pin is None:
                return httpx.Response(404, json={"message": "not found"})
            return httpx.Response(200, json=found_pin)
        if request.method == "DELETE" and "/pins/" in url:
            return httpx.Response(204)
        if request.method == "DELETE" and "/boards/" in url:
            return httpx.Response(204)
        return httpx.Response(404, json={"message": f"unhandled {request.method} {url}"})


async def build_app(
    *,
    capture_events: bool = True,
    settings: Settings | None = None,
) -> tuple[FastAPI, AsyncEngine, InMemoryEventBus, list[EventEnvelope]]:
    """Create an app with a fresh in-memory database.

    Returns (app, engine, bus, captured_events). Call inside the same event
    loop that will drive the scenario.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    bus = InMemoryEventBus()
    captured: list[EventEnvelope] = []

    async def capture(event: EventEnvelope) -> None:
        captured.append(event)

    if capture_events:
        for event_type in (
            "pin:scheduled.v1",
            "pin:published.v1",
            "pin:failed.v1",
            "account:connected.v1",
            "account:disconnected.v1",
        ):
            await bus.subscribe(event_type, capture)

    app = create_app(
        settings=settings or make_settings(),
        session_factory=session_factory,
        token_vault=InMemoryTokenVault(),
    )
    return app, engine, bus, captured


def with_mock_client(service: PinterestService, transport: httpx.MockTransport) -> PinterestService:
    """Wrap a service so its per-account API client uses the mock transport."""

    async def client_for(account):
        provider = await service._token_provider_for(account)  # noqa: SLF001
        from atoz_pinterest_service.domain.client import PinterestApiClient

        return PinterestApiClient(
            base_url=service._settings.pinterest_api_base,  # noqa: SLF001
            account_id=account.id,
            token_provider=provider,
            rate_limiter=service._limiter,  # noqa: SLF001
            timeout_seconds=5.0,
            max_retries=service._settings.max_retries,  # noqa: SLF001
            base_backoff_seconds=0.01,
            max_backoff_seconds=0.05,
            transport=transport,
        )

    service._client_for_account = client_for
    return service


async def connect_account(service, *, niche_id: str, name: str = "hub"):
    """Create and fully connect a Pinterest account via the mock OAuth flow.

    Returns the connected account record (with remote identity populated).
    """
    from urllib.parse import parse_qs, urlparse

    account = await service.create_account(niche_id=niche_id, name=name)
    authorize_url = await service.start_connect(account.id, niche_id=niche_id)
    state = parse_qs(urlparse(authorize_url).query)["state"][0]
    return await service.complete_connect(query_params={"code": "auth-code-1", "state": state})


async def build_repositories(
    *,
    transport: httpx.MockTransport | None = None,
) -> tuple[async_sessionmaker, PinterestService]:
    """In-memory SQLite session factory + service for repository-level tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    service = PinterestService(
        uow_factory=lambda: PinterestService.build_uow(session_factory),
        event_publisher=EventPublisher(InMemoryEventBus(), publisher="pinterest-service"),
        settings=make_settings(),
        token_vault=InMemoryTokenVault(),
        http_client=httpx.AsyncClient(transport=transport) if transport is not None else None,
    )
    if transport is not None:
        service = with_mock_client(service, transport)
    return session_factory, service


async def api_client(app: FastAPI) -> httpx.AsyncClient:
    """Async test client for the given app (same event loop)."""
    from httpx import ASGITransport, AsyncClient

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def scenario(runner: Callable[[], Coroutine[Any, Any, None]]) -> None:
    """Run an async scenario helper through the event loop (no pytest-asyncio)."""
    import asyncio

    asyncio.run(runner())
