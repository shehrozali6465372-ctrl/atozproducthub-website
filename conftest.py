"""Root test fixtures.

All test trees share the ``tests`` directory basename, so conftest modules
would collide; fixtures are centralized here with per-tree names
(``api_*``, ``core_*``, ``svc_*``).
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atoz_backend_core.auth.password import hash_password

SERVICE_PACKAGES = {
    "aios-bridge": "atoz_aios_bridge",
    "content-service": "atoz_content_service",
    "affiliate-service": "atoz_affiliate_service",
    "pinterest-service": "atoz_pinterest_service",
    "seo-service": "atoz_seo_service",
    "analytics-service": "atoz_analytics_service",
    "admin-service": "atoz_admin_service",
    "automation-service": "atoz_automation_service",
}


@pytest.fixture()
def api_app(monkeypatch):
    """Gateway app with test env, JWT secret, and dev credential hash."""
    from atoz_api.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-secret-0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("AUTH_DEV_PASSWORD_HASH", hash_password("test-pass-123"))

    from atoz_api.main import create_app

    return create_app()


@pytest.fixture()
def api_client(api_app):
    with TestClient(api_app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def core_settings():
    from atoz_backend_core.config import BaseServiceSettings

    return BaseServiceSettings(app_env="test", rate_limit_enabled=True)


@pytest.fixture()
def core_client(core_settings):
    from atoz_backend_core import __version__
    from atoz_backend_core.app import create_service_app

    app = create_service_app(
        service_name="backend-core-test",
        version=__version__,
        settings=core_settings,
    )
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def svc_client(request, monkeypatch):
    """Service app client; the package is derived from the test file path."""
    relative = Path(request.module.__file__).resolve().relative_to(Path.cwd().resolve())
    parts = relative.parts
    assert parts[0] == "services" and len(parts) > 1, (
        f"svc_client used outside services: {relative}"
    )
    package = SERVICE_PACKAGES[parts[1]]

    module = __import__(f"{package}.config", fromlist=["get_settings"])
    module.get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "test")

    main = __import__(f"{package}.main", fromlist=["create_app"])
    with TestClient(main.create_app(), raise_server_exceptions=False) as test_client:
        yield test_client
