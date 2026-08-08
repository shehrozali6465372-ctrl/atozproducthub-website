"""Health endpoint tests."""

from atoz_api import __version__


def test_health_ok(api_client) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "atoz-api"
    assert body["version"] == __version__
    assert body["environment"] == "test"


def test_health_has_request_id(api_client) -> None:
    response = api_client.get("/health")
    assert response.headers.get("X-Request-ID")
