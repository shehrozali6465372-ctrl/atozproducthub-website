"""RFC 7807 (problem+json) error handling aligned with the frozen API contracts."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("atoz.errors")

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
