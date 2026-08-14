"""RFC 7807 (problem+json) error handling for the AI OS Bridge.

Mirrors the frozen gateway error model (12-api-contracts.md §6): every
business-layer surface speaks the same error language. The bridge only
raises transport/contract/authentication errors — never AI errors.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("atoz.bridge.errors")

_HTTP_CODE_MAP: dict[int, str] = {
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    422: "VALIDATION_FAILED",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}


class BridgeError(Exception):
    """Application-level error that maps to a problem+json response."""

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail


class ValidationError(BridgeError):
    """422 — payload failed frozen contract validation."""

    def __init__(self, detail: str = "Validation failed.") -> None:
        super().__init__(422, "VALIDATION_FAILED", detail)


class PermissionDeniedError(BridgeError):
    """403 — authenticated transport but not permitted."""

    def __init__(self, detail: str = "Not permitted.") -> None:
        super().__init__(403, "FORBIDDEN", detail)


class ServiceUnavailableError(BridgeError):
    """503 — the AI OS cannot be reached or the circuit is open."""

    def __init__(self, detail: str = "Service dependency is not available.") -> None:
        super().__init__(503, "SERVICE_UNAVAILABLE", detail)


def register_exception_handlers(app: FastAPI) -> None:
    """Register problem+json handlers for BridgeError and framework errors."""

    @app.exception_handler(BridgeError)
    async def bridge_error_handler(request: Request, exc: BridgeError) -> JSONResponse:
        headers = {"X-Request-ID": request.headers.get("X-Request-ID", "")}
        if exc.status_code == 503:
            headers["Retry-After"] = "30"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": "about:blank",
                "title": exc.code,
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
                    for e in exc.errors()
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
