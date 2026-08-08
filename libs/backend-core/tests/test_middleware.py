"""Rate-limit middleware: 429 + Retry-After (API Contracts §7)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from atoz_backend_core.middleware.rate_limit import RateLimitMiddleware


def _app(rate: float, burst: int) -> FastAPI:
    app = FastAPI()

    @app.get("/limited")
    def limited() -> dict[str, str]:
        return {"ok": "true"}

    app.add_middleware(RateLimitMiddleware, enabled=True, rate=rate, burst=burst)
    return app


def test_rate_limit_429_with_retry_after() -> None:
    app = _app(rate=0.0, burst=2)  # zero refill: only the burst is spendable
    with TestClient(app) as core_client:
        first = core_client.get("/limited")
        second = core_client.get("/limited")
        third = core_client.get("/limited")
        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 429
        assert third.headers.get("Retry-After") is not None
        body = third.json()
        assert body["code"] == "RATE_LIMITED"
        assert body["status"] == 429
        assert body["retryable"] is True


def test_rate_limit_exempts_health() -> None:
    from atoz_backend_core.app import create_service_app
    from atoz_backend_core.config import BaseServiceSettings

    app = create_service_app(
        service_name="rl-test",
        version="0.0.0",
        settings=BaseServiceSettings(
            app_env="test",
            rate_limit_enabled=True,
            rate_limit_per_second=0.0,
            rate_limit_burst=0,
        ),
    )
    with TestClient(app) as core_client:
        for _ in range(5):
            assert core_client.get("/health").status_code == 200
