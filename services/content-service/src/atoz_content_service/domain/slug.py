"""Slug helpers — re-exported from the shared backend core (ADR-0003).

Kept as a module so existing content-service imports and tests stay valid;
the canonical implementation lives in ``atoz_backend_core.slug``.
"""

from atoz_backend_core.slug import slugify, unique_slug

__all__ = ["slugify", "unique_slug"]
