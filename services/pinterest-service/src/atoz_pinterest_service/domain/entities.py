"""ORM entities for the Pinterest module (pinterest_db).

Table shapes follow the Database Blueprint §5.2–5.4: every account-scoped
record carries ``niche_id`` AND ``pinterest_account_id`` (blueprint §4
mandatory rules). Ledgers (``pinterest_pins``) are append-only — updates
happen through state fields, never row deletion. Token VALUES are never
stored here: ``pinterest_tokens`` holds only a Vault reference.

No AI data lives here; pin assets are stored out-of-DB and referenced via
``media_ref`` (blueprint §2.1, object storage).
"""

from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from atoz_backend_core.db.base import Base

UUID_LEN = 36


def _utcnow() -> datetime:
    """Python-side ``updated_at`` value (no post-flush expiry)."""
    return datetime.now(UTC)


class PinterestNiche(Base):
    """Local tenant-registry mirror (ADR-0006).

    ``niches`` is owned by content-service in ``content_db``; cross-database
    foreign keys are impossible, so pinterest_db keeps this minimal
    read-only-style mirror for local tenancy lookups and slug-based public
    reads.
    """

    __tablename__ = "pinterest_niches"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class PinterestAccount(Base):
    """One Pinterest account per niche — the root of Pinterest isolation.

    UNIQUE (niche_id, name) per blueprint §4. ``oauth_state`` /
    ``code_verifier`` are temporary connect-flow values (cleared after the
    callback); token VALUES never touch this table.
    """

    __tablename__ = "pinterest_accounts"
    __table_args__ = (
        UniqueConstraint("niche_id", "name", name="uq_pinterest_accounts_niche_name"),
        Index("ix_pinterest_accounts_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    username: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    remote_user_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    scopes: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    oauth_state: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    code_verifier: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    rate_limit_status: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")
    last_rate_limit_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class PinterestToken(Base):
    """OAuth token record — VALUES live in Vault (blueprint §5.2)."""

    __tablename__ = "pinterest_tokens"
    __table_args__ = (
        UniqueConstraint("pinterest_account_id", name="uq_pinterest_tokens_account"),
        Index("ix_pinterest_tokens_status_expires", "status", "access_expires_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_accounts.id"), nullable=False
    )
    vault_ref: Mapped[str] = mapped_column(String(300), nullable=False)
    scopes: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    access_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refresh_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class PinterestBoard(Base):
    """Boards per account, kept in sync with Pinterest (blueprint §5.3)."""

    __tablename__ = "pinterest_boards"
    __table_args__ = (
        UniqueConstraint(
            "pinterest_account_id", "remote_board_id", name="uq_pinterest_boards_account_remote"
        ),
        Index(
            "ix_pinterest_boards_niche_account_status", "niche_id", "pinterest_account_id", "status"
        ),
        Index("ix_pinterest_boards_niche_name", "niche_id", "pinterest_account_id", "name"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_accounts.id"), nullable=False
    )
    remote_board_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    sync_state: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class BoardSection(Base):
    """Board sections per account/board (Pinterest API v5 sections)."""

    __tablename__ = "board_sections"
    __table_args__ = (
        UniqueConstraint(
            "pinterest_account_id", "remote_section_id", name="uq_board_sections_account_remote"
        ),
        Index("ix_board_sections_board_id", "pinterest_board_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_accounts.id"), nullable=False
    )
    pinterest_board_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_boards.id"), nullable=False
    )
    remote_section_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class PinterestPin(Base):
    """Append-only pin ledger (blueprint §5.4) — every published pin ever."""

    __tablename__ = "pinterest_pins"
    __table_args__ = (
        UniqueConstraint(
            "pinterest_account_id", "remote_pin_id", name="uq_pinterest_pins_account_remote"
        ),
        UniqueConstraint(
            "niche_id",
            "pinterest_account_id",
            "checksum",
            name="uq_pinterest_pins_niche_account_checksum",
        ),
        Index(
            "ix_pinterest_pins_niche_account_status_sched",
            "niche_id",
            "pinterest_account_id",
            "status",
            "scheduled_at",
        ),
        Index("ix_pinterest_pins_published_at", "published_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_accounts.id"), nullable=False
    )
    pinterest_board_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_boards.id"), nullable=True
    )
    # Cross-database reference (content_db.articles) — plain indexed column,
    # no FK (ADR-0006 local mirror policy).
    article_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    remote_pin_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    media_ref: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    pin_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    destination_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    link: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    utms_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    checksum: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class PinQueueItem(Base):
    """Durable record of every scheduled pin publish job (blueprint §5.4).

    Redis holds the working set; this table is the source of truth.
    """

    __tablename__ = "pin_queue_items"
    __table_args__ = (
        UniqueConstraint("pinterest_pin_id", name="uq_pin_queue_items_pin"),
        Index("ix_pin_queue_items_state_run_at", "state", "run_at"),
        Index(
            "ix_pin_queue_items_niche_account_state", "niche_id", "pinterest_account_id", "state"
        ),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_accounts.id"), nullable=False
    )
    pinterest_pin_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_pins.id"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class PinPublishAttempt(Base):
    """Complete publishing attempt record — every attempt, never rewritten."""

    __tablename__ = "pin_publish_attempts"
    __table_args__ = (
        Index("ix_pin_publish_attempts_pin_attempt", "pinterest_pin_id", "attempt_no"),
        Index(
            "ix_pin_publish_attempts_niche_account_status",
            "niche_id",
            "pinterest_account_id",
            "status",
        ),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_accounts.id"), nullable=False
    )
    pinterest_pin_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_pins.id"), nullable=False
    )
    pin_queue_item_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("pin_queue_items.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    remote_pin_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_kind: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    error_detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PinterestAnalytics(Base):
    """Per-account Pinterest business metrics — business data only (blueprint §4/§5)."""

    __tablename__ = "pinterest_analytics"
    __table_args__ = (
        UniqueConstraint(
            "niche_id",
            "pinterest_account_id",
            "metric_date",
            name="uq_pinterest_analytics_account_date",
        ),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("pinterest_accounts.id"), nullable=False
    )
    metric_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    saves: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outbound_clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engagement: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )
