"""API v1 versioning: all business routes live under /api/v1."""


def test_v1_routes_in_openapi(api_client) -> None:
    paths = api_client.get("/openapi.json").json()["paths"]
    assert "/api/v1/auth/token" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/revoke" in paths
    assert "/api/v1/auth/me" in paths
    assert "/health" in paths


def test_unversioned_business_route_not_served(api_client) -> None:
    response = api_client.get("/auth/me")
    assert response.status_code == 404
