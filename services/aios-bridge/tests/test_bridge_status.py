"""Bridge status endpoint (non-secret transport metadata only)."""


def test_bridge_status(svc_client) -> None:
    response = svc_client.get("/bridge/status")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "aios-bridge"
    assert body["status"] == "ok"
    assert "aios_base_url" in body
    assert "hmac_signing_enabled" in body
    assert "aios_api_key" not in body
