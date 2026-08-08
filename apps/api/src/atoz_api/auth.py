"""Gateway authentication: session manager wiring and auth context.

Bearer tokens are decoded and sessions resolved by ``AuthMiddleware``;
protected routes consume ``request.state.auth`` via the shared RBAC
dependency (``atoz_backend_core.auth``). Phase 5 replaces the dev identity
with OIDC — the transport here stays.
"""

from dataclasses import dataclass

from atoz_api.config import Settings
from atoz_backend_core.auth import (
    InMemorySessionManager,
    RedisSessionManager,
    SessionManager,
)


@dataclass(frozen=True)
class AuthenticatedContext:
    """Concrete AuthContext attached to ``request.state.auth``."""

    subject: str
    permissions: tuple[str, ...]
    session_id: str


def build_session_manager(settings: Settings) -> SessionManager:
    """In-memory sessions for dev/tests; Redis-backed when configured."""
    if settings.redis_url:
        return RedisSessionManager(settings.redis_url)
    return InMemorySessionManager()
