"""Health endpoint tests for seo-service."""

from atoz_seo_service import __version__


def test_health_ok(svc_client) -> None:
    response = svc_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "seo-service"
    assert body["version"] == __version__
    assert body["environment"] == "test"


def test_health_has_request_id(svc_client) -> None:
    response = svc_client.get("/health")
    assert response.headers.get("X-Request-ID")
