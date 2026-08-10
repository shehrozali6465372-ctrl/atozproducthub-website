"""Pydantic request/response schemas for the Pinterest module.

Response models deliberately omit token VALUES: only vault refs, scopes,
and expiry metadata are exposed (Database Blueprint §5.2, Task 16 rule —
never expose tokens to frontend or logs).
"""

import re
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


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


# ------------------------------------------------------------------ accounts
class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    username: str = Field(default="", max_length=200)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    username: str | None = Field(default=None, max_length=200)


class AccountOut(BaseModel):
    id: str
    niche_id: str
    name: str
    username: str
    remote_user_id: str
    status: str
    scopes: str
    rate_limit_status: str
    last_rate_limit_at: datetime | None = None
    connected_at: datetime | None = None
    error: str
    created_at: datetime
    updated_at: datetime


class AccountStatusOut(BaseModel):
    account_id: str
    niche_id: str
    name: str
    status: str
    connected_at: datetime | None = None
    rate_limit_status: str
    last_rate_limit_at: datetime | None = None
    token_status: str | None = None
    token_expires_at: datetime | None = None
    board_count: int
    pin_counts: dict[str, int]


class ConnectStartOut(BaseModel):
    account_id: str
    authorize_url: str


# ------------------------------------------------------------------- boards
class BoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=1000)


class BoardOut(BaseModel):
    id: str
    niche_id: str
    pinterest_account_id: str
    remote_board_id: str
    name: str
    description: str
    status: str
    sync_state: str
    last_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------- pins
class PinCreate(BaseModel):
    board_id: str
    title: str = Field(min_length=1, max_length=500)
    destination_url: str = Field(min_length=1, max_length=2000)
    media_ref: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=2000)
    link: str = Field(default="", max_length=2000)
    article_id: str | None = None
    scheduled_at: datetime | None = None
    utms: dict[str, str] = Field(default_factory=dict)


class PinOut(BaseModel):
    id: str
    niche_id: str
    pinterest_account_id: str
    pinterest_board_id: str | None
    article_id: str | None
    remote_pin_id: str | None
    media_ref: str
    pin_url: str
    destination_url: str
    title: str
    description: str
    link: str
    status: str
    scheduled_at: datetime | None
    published_at: datetime | None
    utms_json: str
    checksum: str | None
    created_at: datetime
    updated_at: datetime


class QueueItemOut(BaseModel):
    id: str
    niche_id: str
    pinterest_account_id: str
    pinterest_pin_id: str
    state: str
    attempts: int
    run_at: datetime
    completed_at: datetime | None
    error: str
    created_at: datetime
    updated_at: datetime


class PublishAttemptOut(BaseModel):
    id: str
    niche_id: str
    pinterest_account_id: str
    pinterest_pin_id: str
    pin_queue_item_id: str | None
    status: str
    attempt_no: int
    remote_pin_id: str | None
    http_status: int | None
    error_kind: str
    error_detail: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


# ---------------------------------------------------------------- analytics
class AnalyticsUpsert(BaseModel):
    metric_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    impressions: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    outbound_clicks: int = Field(default=0, ge=0)
    engagement: int = Field(default=0, ge=0)


class AnalyticsOut(BaseModel):
    id: str
    niche_id: str
    pinterest_account_id: str
    metric_date: str
    impressions: int
    saves: int
    clicks: int
    outbound_clicks: int
    engagement: int
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------------- public
class PublicPinOut(BaseModel):
    id: str
    slug: str = ""
    title: str
    description: str
    board: str = ""
    account_name: str = ""
    destination_url: str
    pin_url: str
    published_at: datetime | None
    saves: str = ""


class PublicBoardOut(BaseModel):
    id: str
    remote_board_id: str
    name: str
    description: str


class PublicAccountOut(BaseModel):
    id: str
    name: str
    username: str
    status: str
