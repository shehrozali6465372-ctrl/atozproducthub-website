"""Readiness endpoint tests for aios-bridge (dependencies unconfigured in M3)."""


def test_ready_reports_not_configured(svc_client) -> None:
    response = svc_client.get("/ready")
    assert response.status_code == 200
    components = {c["name"]: c["status"] for c in response.json()["components"]}
    assert components == {"postgres": "not_configured", "redis": "not_configured"}
