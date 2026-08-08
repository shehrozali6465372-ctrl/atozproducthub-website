"""Shared app factory: /health, /ready, /metrics, request ID, security headers."""

from atoz_backend_core import __version__


def test_health_ok(core_client) -> None:
    response = core_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "backend-core-test"
    assert body["version"] == __version__
    assert body["environment"] == "test"


def test_health_has_request_id(core_client) -> None:
    response = core_client.get("/health")
    assert response.headers.get("X-Request-ID")


def test_ready_reports_not_configured(core_client) -> None:
    response = core_client.get("/ready")
    assert response.status_code == 200
    components = {c["name"]: c["status"] for c in response.json()["components"]}
    assert components == {"postgres": "not_configured", "redis": "not_configured"}


def test_metrics_exposed(core_client) -> None:
    response = core_client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_security_headers(core_client) -> None:
    response = core_client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" not in response.headers  # dev only


def test_openapi_metadata(core_client) -> None:
    response = core_client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["version"] == __version__
