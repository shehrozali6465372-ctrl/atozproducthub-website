"""Readiness endpoint tests (dependencies unconfigured in M3)."""


def test_ready_reports_not_configured(api_client) -> None:
    response = api_client.get("/ready")
    assert response.status_code == 200
    components = {c["name"]: c["status"] for c in response.json()["components"]}
    assert components == {"postgres": "not_configured", "redis": "not_configured"}
