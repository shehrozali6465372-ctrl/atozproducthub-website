"""Security response headers middleware (secure headers by default)."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Paths whose interactive content (Swagger UI) needs inline styles.
DOC_PATHS = ("/docs", "/redoc", "/openapi.json", "/metrics")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply standard security headers; HSTS only in production.

    CSP is skipped on interactive documentation paths so the OpenAPI UI
    remains usable.
    """

    def __init__(self, app, *, production: bool) -> None:
        super().__init__(app)
        self._hsts = "max-age=31536000; includeSubDomains" if production else None

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )
        if self._hsts and not request.url.scheme.startswith("http://"):
            response.headers["Strict-Transport-Security"] = self._hsts
        if not request.url.path.startswith(DOC_PATHS):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self'"
            )
        return response
