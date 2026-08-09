"""Domain layer of the content module: enums, entities, lifecycle rules.

Pure business logic — no framework imports, no database I/O, no AI.
"""

from atoz_content_service.domain.entities import (
    Article,
    ArticleCategory,
    ArticleTag,
    ArticleVersion,
    Category,
    Niche,
    Tag,
)
from atoz_content_service.domain.enums import (
    ArticleStatus,
    CategoryStatus,
    NicheStatus,
    TagStatus,
)
from atoz_content_service.domain.lifecycle import (
    TRANSITIONS,
    can_transition,
    transition,
)

__all__ = [
    "Article",
    "ArticleCategory",
    "ArticleStatus",
    "ArticleTag",
    "ArticleVersion",
    "Category",
    "CategoryStatus",
    "Niche",
    "NicheStatus",
    "TRANSITIONS",
    "Tag",
    "TagStatus",
    "can_transition",
    "transition",
]
