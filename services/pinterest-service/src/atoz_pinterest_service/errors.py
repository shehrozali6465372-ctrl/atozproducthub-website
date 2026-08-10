"""RFC 7807 (problem+json) error handling for pinterest-service.

Mirrors the frozen gateway error model (12-api-contracts.md §6) and the
affiliate/content service conventions so every surface of the business
layer speaks the same error language.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("atoz.pinterest.errors")

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


class NotFoundError(AppError):
    """404 — entity or context unknown (kept indistinguishable for tokens)."""

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


class AccountIsolationError(AppError):
    """422 — account-scoped operation attempted without account context."""

    def __init__(self, detail: str = "Pinterest account context is required.") -> None:
        super().__init__(422, "ACCOUNT_CONTEXT_REQUIRED", detail)


class RateLimitExceededError(AppError):
    """429 — per-account Pinterest rate budget exhausted."""

    def __init__(self, detail: str = "Pinterest rate limit reached for this account.") -> None:
        super().__init__(429, "RATE_LIMITED", detail, retryable=True)


class RemoteApiError(AppError):
    """502/503 — Pinterest API failure (retryable or not)."""

    def __init__(
        self, detail: str = "Pinterest API request failed.", *, retryable: bool = True
    ) -> None:
        super().__init__(503 if retryable else 502, "REMOTE_API_ERROR", detail, retryable=retryable)


class OAuthError(AppError):
    """400 — OAuth state/CSRF or callback validation failure."""

    def __init__(self, detail: str = "OAuth flow failed.") -> None:
        super().__init__(400, "OAUTH_FAILED", detail)


class ServiceUnavailableError(AppError):
    """503 — required dependency (e.g. database) is not configured."""

    def __init__(self, detail: str = "Service is not fully configured.") -> None:
        super().__init__(503, "SERVICE_UNAVAILABLE", detail, retryable=True)


def _problem(
    *,
    status: int,
    code: str,
    detail: str,
    instance: str,
    retryable: bool = False,
    title: str | None = None,
) -> dict[str, Any]:
    return {
        "type": f"https://atozproducthub.dev/errors/{code.lower()}",
        "title": title or code.replace("_", " ").title(),
        "status": status,
        "code": code,
        "detail": detail,
        "instance": instance,
        "retryable": retryable,
    }


def _instance(request: Request) -> str:
    return request.headers.get("X-Request-ID") or request.url.path


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the RFC 7807 handlers used by every pinterest route."""

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("request_validation_failed", extra={"errors": exc.errors()})
        return JSONResponse(
            status_code=422,
            content=_problem(
                status=422,
                code="VALIDATION_FAILED",
                detail="Request validation failed.",
                instance=_instance(request),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=_problem(
                status=exc.status_code,
                code=code,
                detail=str(exc.detail),
                instance=_instance(request),
            ),
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("app_error", extra={"code": exc.code, "detail": exc.detail})
        return JSONResponse(
            status_code=exc.status_code,
            content=_problem(
                status=exc.status_code,
                code=exc.code,
                detail=exc.detail,
                instance=_instance(request),
                retryable=exc.retryable,
                title=exc.title,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_problem(
                status=500,
                code="INTERNAL_ERROR",
                detail="An unexpected error occurred.",
                instance=_instance(request),
                retryable=True,
            ),
        )
