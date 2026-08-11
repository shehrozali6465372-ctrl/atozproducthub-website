"""Canonical URL policy: path normalization + duplicate-URL prevention.

The URL registry enforces ``UNIQUE (niche_id, path)``; this module builds
canonical paths from entity type + slug and normalizes incoming paths so
two spellings of the same URL never become two indexable URLs.
"""

import re

from atoz_seo_service.errors import ValidationError

_PATH_PART = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_path(path: str) -> str:
    """Normalize a URL path: lowercase, collapse slashes, strip query/hash."""
    raw = path.strip().split("?", 1)[0].split("#", 1)[0]
    if not raw.startswith("/"):
        raw = f"/{raw}"
    parts = [part for part in raw.split("/") if part]
    lowered = "/".join(part.lower() for part in parts)
    return f"/{lowered}" if lowered else "/"


def entity_path(*, entity_type: str, slug: str) -> str:
    """Build the canonical public path for a business entity."""
    if not _PATH_PART.match(slug):
        raise ValidationError(f"Invalid slug for {entity_type}: {slug!r}.")
    prefixes = {
        "article": "articles",
        "product": "products",
        "category": "categories",
        "tag": "tags",
        "landing": "landing",
        "collection": "collections",
        "page": "",
    }
    prefix = prefixes.get(entity_type)
    if prefix is None:
        raise ValidationError(f"Unknown entity type: {entity_type}.")
    if prefix == "":
        return f"/{slug}"
    return f"/{prefix}/{slug}"


def canonical_url(*, public_base_url: str, path: str) -> str:
    """Absolute canonical URL for a normalized path."""
    return f"{public_base_url.rstrip('/')}{normalize_path(path)}"
