"""Gateway middleware: Bearer authentication + request ID.

``RequestContextMiddleware`` re-exports the shared request-ID middleware
(backend-core, ADR-0003). ``AuthMiddleware`` decodes Bearer access tokens
and resolves the session, attaching ``request.state.auth`` for RBAC.
"""

from atoz_api.auth import AuthenticatedContext
from atoz_api.config import get_settings
from atoz_backend_core.middleware.request_id import RequestIdMiddleware

RequestContextMiddleware = RequestIdMiddleware


class AuthMiddleware:
    """Decode Bearer access tokens and attach the auth context (no hard failure).

    Unauthenticated requests pass through untouched; protected routes enforce
    via the RBAC dependency. Token/session errors simply mean "no context".
    """

    def __init__(self, app, settings=None, session_manager=None) -> None:
        self._app = app
        self._settings = settings or get_settings()
        self._session_manager = session_manager

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = dict(
            (k.decode("latin-1"), v.decode("latin-1")) for k, v in scope.get("headers", [])
        )
        authorization = headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization[len("Bearer ") :]
            context = await self._resolve(token)
            if context is not None:
                scope.setdefault("state", {})["auth"] = context
        await self._app(scope, receive, send)

    async def _resolve(self, token: str) -> AuthenticatedContext | None:
        from jwt import PyJWTError

        from atoz_backend_core.auth import decode_token

        try:
            claims = decode_token(token, secret=self._settings.jwt_secret, expected_type="access")
        except PyJWTError:
            return None
        if self._session_manager is None:
            return None
        session = await self._session_manager.get(claims.session_id)
        if session is None:
            return None
        return AuthenticatedContext(
            subject=session.subject,
            permissions=session.permissions,
            session_id=session.session_id,
        )
