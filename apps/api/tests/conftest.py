"""Shared fixtures for foundation tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app(monkeypatch):
    from atoz_api.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "test")

    from atoz_api.main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    # raise_server_exceptions=False so 500 responses (problem+json) are assertable.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
