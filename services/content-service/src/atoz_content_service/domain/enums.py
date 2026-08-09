"""Content module enumerations (string constants, portable across SQLite/Postgres)."""

from enum import StrEnum


class NicheStatus(StrEnum):
    """Niche lifecycle (Database Blueprint §5.1)."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ArticleStatus(StrEnum):
    """Article lifecycle.

    The Database Blueprint defines draft/review/published/unpublished; M4
    adds ``archived`` for the required draft → review → published → archived
    lifecycle (ADR-0004).
    """

    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    ARCHIVED = "archived"


class CategoryStatus(StrEnum):
    """Category availability within a niche."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class TagStatus(StrEnum):
    """Tag availability within a niche."""

    ACTIVE = "active"
    ARCHIVED = "archived"
