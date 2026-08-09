"""Slug generation and per-niche uniqueness (Database Blueprint §4.3).

Slugs are ASCII, lowercase, hyphen-separated, and unique per niche
(``UNIQUE (niche_id, slug)``). ``slugify`` is deterministic and portable —
no locale-dependent transliteration, so the same title always yields the
same slug in every environment.
"""

import re

_NON_ASCII = re.compile(r"[^a-z0-9]+")
_EDGE = re.compile(r"^[-]+|[-]+$")


def slugify(text: str) -> str:
    """Turn arbitrary text into an ASCII slug.

    Non-ASCII characters are dropped (ASCII-only policy); runs of
    non-alphanumeric characters collapse to a single hyphen.
    """
    normalized = _NON_ASCII.sub("-", text.lower())
    slug = _EDGE.sub("", normalized)
    return slug or "untitled"


def unique_slug(desired: str, *, taken: set[str]) -> str:
    """Return ``desired`` or ``desired-2``, ``desired-3``, ... when taken."""
    if desired not in taken:
        return desired
    index = 2
    while f"{desired}-{index}" in taken:
        index += 1
    return f"{desired}-{index}"
