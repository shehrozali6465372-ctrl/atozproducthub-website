"""Prometheus metrics endpoint tests."""


def test_metrics_exposed(api_client) -> None:
    response = api_client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
