"""Request-ID middleware: correlation ID on every request and response."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from atoz_backend_core.logging import request_id_var

logger = logging.getLogger("atoz.http")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a request ID, expose it on the response, and log every request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info(
                "request_completed",
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "status": response.status_code if response is not None else 500,
                        "duration_ms": round(elapsed_ms, 2),
                    }
                },
            )
            request_id_var.reset(token)
        if response is not None:
            response.headers["X-Request-ID"] = request_id
        return response
