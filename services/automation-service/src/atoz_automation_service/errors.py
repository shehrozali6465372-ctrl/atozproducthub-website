"""RFC 7807 (problem+json) error handling for automation-service.

Mirrors the frozen gateway error model (12-api-contracts.md §6) and the
content/affiliate/pinterest/seo/analytics service conventions so every
surface of the business layer speaks the same error language.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("atoz.automation.errors")

_HTTP_CODE_MAP: dict[int, str] = {
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "DUPLICATE",
    422: "VALIDATION_FAILED",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}


class AppError(Exception):
    """Application-level error that maps to a problem+json response."""

    def __init__(
        self,
        status_code: int,
        code: str,
        detail: str,
        *,
        retryable: bool = False,
        title: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.retryable = retryable
        self.title = title


class AuthenticationError(AppError):
    """401 — missing or invalid credentials."""

    def __init__(self, detail: str = "Authentication required.") -> None:
        super().__init__(401, "UNAUTHENTICATED", detail)


class PermissionDeniedError(AppError):
    """403 — authenticated but not permitted."""

    def __init__(self, detail: str = "Not permitted.") -> None:
        super().__init__(403, "FORBIDDEN", detail)


class MfaRequiredError(AppError):
    """403 — privileged action requires a verified MFA session."""

    def __init__(self, detail: str = "MFA verification is required for this action.") -> None:
        super().__init__(403, "MFA_REQUIRED", detail)


class NotFoundError(AppError):
    """404 — entity or context unknown."""

    def __init__(self, detail: str = "Entity not found.") -> None:
        super().__init__(404, "NOT_FOUND", detail)


class DuplicateError(AppError):
    """409 — unique constraint or in-use conflict."""

    def __init__(self, detail: str = "Duplicate entity.") -> None:
        super().__init__(409, "DUPLICATE", detail)


class ValidationError(AppError):
    """422 — lifecycle/tenancy/business validation failure."""

    def __init__(self, detail: str = "Validation failed.") -> None:
        super().__init__(422, "VALIDATION_FAILED", detail)


class UnsupportedNicheError(AppError):
    """422 — niche not registered or not active (frozen code)."""

    def __init__(self, detail: str = "Niche is not registered or active.") -> None:
        super().__init__(422, "UNSUPPORTED_NICHE", detail)


class ServiceUnavailableError(AppError):
    """503 — dependency (sibling service probe) not configured."""

    def __init__(self, detail: str = "Service dependency is not configured.") -> None:
        super().__init__(503, "SERVICE_UNAVAILABLE", detail)


def register_exception_handlers(app: FastAPI) -> None:
    """Register problem+json handlers for AppError and framework errors."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        headers = {"X-Request-ID": request.headers.get("X-Request-ID", "")}
        if exc.retryable:
            headers["Retry-After"] = "30"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": "about:blank",
                "title": exc.title or exc.code,
                "status": exc.status_code,
                "code": exc.code,
                "detail": exc.detail,
            },
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        return JSONResponse(
            status_code=422,
            content={
                "type": "about:blank",
                "title": "VALIDATION_FAILED",
                "status": 422,
                "code": "VALIDATION_FAILED",
                "detail": "Request validation failed.",
                "errors": [
                    {
                        "loc": list(e.get("loc", [])),
                        "msg": e.get("msg", ""),
                        "type": e.get("type", ""),
                    }
                    for e in errors
                ],
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": "about:blank",
                "title": code,
                "status": exc.status_code,
                "code": code,
                "detail": str(exc.detail),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank",
                "title": "INTERNAL_ERROR",
                "status": 500,
                "code": "INTERNAL_ERROR",
                "detail": "An internal error occurred.",
            },
        )
