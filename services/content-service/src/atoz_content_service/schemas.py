"""Request/response schemas for the content API (12-api-contracts.md §5-6).

DTOs follow the frozen conventions: RFC 7807 errors, versioned routes,
pagination with a hard ``page_size`` cap, and niche-aware payloads.
"""

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

StatusValue = Literal["draft", "review", "published", "unpublished", "archived"]
NicheStatusValue = Literal["draft", "active", "archived"]
TaxonomyStatusValue = Literal["active", "archived"]
LifecycleAction = Literal[
    "submit", "approve", "reject", "publish", "unpublish", "archive", "restore"
]

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class Page(BaseModel, Generic[T]):
    """Pagination envelope: ``{items, page, page_size, total}``."""

    items: list[T]
    page: int
    page_size: int
    total: int


# --------------------------------------------------------------- niches
class NicheCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    default_currency: str | None = Field(default=None, min_length=3, max_length=3)


class NicheUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    status: NicheStatusValue | None = None
    default_currency: str | None = Field(default=None, min_length=3, max_length=3)


class NicheOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    status: str
    default_currency: str | None
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------- categories
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    parent_id: str | None = Field(default=None, pattern=UUID_PATTERN)
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: str | None = Field(default=None, pattern=UUID_PATTERN)
    sort_order: int | None = None
    status: TaxonomyStatusValue | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    parent_id: str | None
    name: str
    slug: str
    description: str
    path: str | None
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime


class PublicCategoryOut(BaseModel):
    slug: str
    name: str
    description: str


# ------------------------------------------------------------------- tags
class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    status: TaxonomyStatusValue | None = None


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    name: str
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime


class PublicTagOut(BaseModel):
    slug: str
    name: str


# --------------------------------------------------------------- articles
class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    excerpt: str = Field(default="", max_length=2000)
    body: str = ""
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    category_ids: list[str] = Field(default_factory=list)
    primary_category_id: str | None = Field(default=None, pattern=UUID_PATTERN)
    tag_ids: list[str] = Field(default_factory=list)
    change_summary: str | None = Field(default=None, max_length=500)


class ArticleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    excerpt: str | None = Field(default=None, max_length=2000)
    body: str | None = None
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    category_ids: list[str] | None = None
    primary_category_id: str | None = Field(default=None, pattern=UUID_PATTERN)
    tag_ids: list[str] | None = None
    change_summary: str | None = Field(default=None, max_length=500)


class LifecycleRequest(BaseModel):
    action: LifecycleAction


class CategoryRefOut(BaseModel):
    id: str
    slug: str
    name: str
    is_primary: bool


class TagRefOut(BaseModel):
    id: str
    slug: str
    name: str


class VersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    article_id: str
    version_no: int
    title: str
    excerpt: str
    content_ref: str
    checksum: str
    change_summary: str | None
    created_by: str | None
    created_at: datetime


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    slug: str
    title: str
    excerpt: str
    status: str
    content_ref: str | None
    content_checksum: str | None
    author_ref: str | None
    editor_ref: str | None
    primary_category_id: str | None
    published_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PublicArticleOut(BaseModel):
    id: str
    slug: str
    title: str
    excerpt: str
    category: PublicCategoryOut | None
    tags: list[PublicTagOut]
    read_time_minutes: int
    published_at: datetime
    body: list[str]


class PublicNicheOut(BaseModel):
    id: str
    slug: str
    name: str


class ArticleListItemOut(BaseModel):
    """Admin list row: article metadata only (no body, no links)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    slug: str
    title: str
    excerpt: str
    status: str
    author_ref: str | None
    editor_ref: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ArticleDetailOut(BaseModel):
    """Admin detail view: article + taxonomy + version history."""

    article: ArticleOut
    categories: list[CategoryRefOut]
    tags: list[TagRefOut]
    versions: list[VersionOut]
