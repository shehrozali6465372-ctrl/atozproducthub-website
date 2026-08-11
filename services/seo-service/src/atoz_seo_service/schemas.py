"""Pydantic schemas for the SEO module (public + admin APIs)."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int = 1
    page_size: int = 20
    total: int = 0


# -------------------------------------------------------------------- niches
class NicheMirrorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")


class NicheMirrorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern="^(draft|active|archived)$")


# ------------------------------------------------------------------ metadata
class UrlRegisterIn(BaseModel):
    entity_type: str = Field(pattern="^(article|product|category|tag|landing|collection|page)$")
    entity_id: str = Field(min_length=1, max_length=36)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    path: str | None = Field(default=None, min_length=1, max_length=500)
    status: str = Field(default="active", pattern="^(active|redirect|removed|hidden)$")


class UrlOut(BaseModel):
    id: str
    niche_id: str
    path: str
    canonical_path: str
    entity_type: str
    entity_id: str
    redirect_to: str = ""
    status: str
    changed_at: datetime | None = None

    model_config = {"from_attributes": True}


class MetadataUpsertIn(BaseModel):
    title: str = Field(default="", max_length=500)
    meta_description: str = Field(default="", max_length=1000)
    robots: str = Field(
        default="index,follow",
        pattern="^(index,follow|noindex,follow|noindex,nofollow|index,nofollow)$",
    )
    og: dict[str, Any] = Field(default_factory=dict)
    structured_data: list[dict[str, Any]] = Field(default_factory=list)


class MetadataOut(BaseModel):
    id: str
    niche_id: str
    url_registry_id: str
    title: str
    meta_description: str
    canonical_url: str
    robots: str
    og_json: str
    structured_data_json: str
    checksum: str
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PublicMetadataOut(BaseModel):
    title: str
    description: str
    canonical_url: str
    robots: str
    og: dict[str, Any] = Field(default_factory=dict)
    structured_data: list[dict[str, Any]] = Field(default_factory=list)


# ------------------------------------------------------------------ sitemaps
class SitemapShardOut(BaseModel):
    id: str
    niche_id: str
    group_name: str
    shard_no: int
    object_ref: str
    url_count: int
    generated_at: datetime | None = None
    status: str
    last_url: str

    model_config = {"from_attributes": True}


class SitemapRebuildOut(BaseModel):
    group: str
    shard_count: int
    shards: list[dict[str, Any]] = Field(default_factory=list)


# ------------------------------------------------------------------ search
class SearchDocumentIn(BaseModel):
    id: str = Field(min_length=1, max_length=36)
    type: str = Field(pattern="^(article|product|category|tag|landing|collection)$")
    slug: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    excerpt: str = Field(default="", max_length=2000)
    url: str = Field(default="", max_length=700)
    tags: list[str] = Field(default_factory=list)
    price_cents: int | None = Field(default=None, ge=0)
    published_at: str | None = None


class SearchHitOut(BaseModel):
    id: str
    type: str
    slug: str
    title: str
    excerpt: str
    url: str
    score: float = 0.0


class SearchPageOut(Page[SearchHitOut]):
    pass


# ------------------------------------------------------------ crawl reports
class CrawlReportIn(BaseModel):
    source: str = Field(pattern="^(gsc|bing)$")
    report_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    pages_indexed: int = Field(default=0, ge=0)
    impressions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    position_avg: float = Field(default=0.0, ge=0.0)
    raw: dict[str, Any] = Field(default_factory=dict)


class CrawlReportOut(BaseModel):
    id: str
    niche_id: str
    source: str
    report_date: str
    pages_indexed: int
    impressions: int
    clicks: int
    position_avg: float
    raw_json: str

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------- events
class EventWebhookIn(BaseModel):
    type: str
    event_id: str = Field(default="", max_length=100)
    aggregate_id: str = Field(default="", max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
