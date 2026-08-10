"""UUID v7 generation — re-exported from the shared backend core (ADR-0003).

Kept as a module so existing content-service imports and tests stay valid;
the canonical implementation lives in ``atoz_backend_core.uuids``.
"""

from atoz_backend_core.uuids import uuid7

__all__ = ["uuid7"]
