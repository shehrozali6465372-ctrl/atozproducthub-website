"""Authentication foundation tests: token, refresh, revoke, me (dev placeholder)."""

from fastapi.testclient import TestClient


def _token(api_client, username="dev-admin", password="test-pass-123"):
    return api_client.post(
        "/api/v1/auth/token",
        json={"username": username, "password": password},
    )


def test_token_flow(api_client) -> None:
    response = _token(api_client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] == 900


def test_token_rejects_bad_password(api_client) -> None:
    response = _token(api_client, password="wrong-password")
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_token_rejects_unknown_user(api_client) -> None:
    response = _token(api_client, username="nobody")
    assert response.status_code == 401


def test_me_requires_valid_token(api_client) -> None:
    assert api_client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_identity(api_client) -> None:
    token = _token(api_client).json()["access_token"]
    response = api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["subject"] == "dev-admin"
    assert "auth:read" in body["permissions"]
    assert body["session_id"]


def test_refresh_rotates_tokens(api_client) -> None:
    refresh = _token(api_client).json()["refresh_token"]
    response = api_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"] != refresh


def test_refresh_rejects_invalid_token(api_client) -> None:
    response = api_client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert response.status_code == 401


def test_revoke_invalidates_session(api_client) -> None:
    body = _token(api_client).json()
    access, refresh = body["access_token"], body["refresh_token"]
    assert (
        api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}).status_code
        == 200
    )

    revoke = api_client.post("/api/v1/auth/revoke", json={"refresh_token": refresh})
    assert revoke.status_code == 204

    # Session gone: both access (via session check) and refresh fail.
    assert (
        api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}).status_code
        == 401
    )
    refreshed = api_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert refreshed.status_code == 401


def test_token_disabled_in_production(monkeypatch) -> None:
    from atoz_api.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("JWT_SECRET", "test-secret-0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("AUTH_DEV_PASSWORD_HASH", "irrelevant")
    # M11 secrets guard: prod must not boot with the dev-only subject default.
    monkeypatch.setenv("AUTH_DEV_SUBJECT", "disabled-in-prod")

    from atoz_api.main import create_app

    with TestClient(create_app(), raise_server_exceptions=False) as prod_client:
        response = prod_client.post(
            "/api/v1/auth/token",
            json={"username": "dev-admin", "password": "whatever"},
        )
        assert response.status_code == 501
