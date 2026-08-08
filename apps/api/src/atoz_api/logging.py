"""Structured JSON logging — shared implementation (backend-core).

Re-exported so existing imports keep working; the implementation lives in
``atoz_backend_core.logging`` (ADR-0003, no duplication).
"""

from atoz_backend_core.logging import JsonFormatter, configure_logging, request_id_var

__all__ = ["JsonFormatter", "configure_logging", "request_id_var"]
