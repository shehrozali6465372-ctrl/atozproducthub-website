"""pinterest_db tables: niches mirror, accounts, tokens, boards, sections,
pins, queue items, publish attempts, per-account analytics

Revision ID: 0001
Revises:
Create Date: 2026-08-10

Portable schema (SQLite in tests, PostgreSQL in prod/CI). Primary keys are
UUID v7 strings assigned by the domain layer (ADR-0004/0006). Every
account-scoped table carries ``niche_id`` AND ``pinterest_account_id`` per
Database Blueprint §4 mandatory rules. Token VALUES never live here —
``pinterest_tokens`` stores only a Vault reference (blueprint §5.2).
``pinterest_pins`` is an append-only ledger (blueprint §5.4).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TS = sa.DateTime(timezone=True)
NOW = sa.text("CURRENT_TIMESTAMP")
UUID = sa.String(36)


def upgrade() -> None:
    # ------------------------------------------- local tenancy mirror (ADR-0006)
    op.create_table(
        "pinterest_niches",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("ix_pinterest_niches_slug", "pinterest_niches", ["slug"], unique=True)

    # ------------------------------------------------------------ accounts
    op.create_table(
        "pinterest_accounts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("username", sa.String(200), nullable=False, server_default=""),
        sa.Column("remote_user_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("scopes", sa.String(500), nullable=False, server_default=""),
        sa.Column("oauth_state", sa.String(128), nullable=False, server_default=""),
        sa.Column("code_verifier", sa.String(200), nullable=False, server_default=""),
        sa.Column("rate_limit_status", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("last_rate_limit_at", TS, nullable=True),
        sa.Column("connected_at", TS, nullable=True),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_pinterest_accounts_niche_name", "pinterest_accounts", ["niche_id", "name"], unique=True
    )
    op.create_index(
        "ix_pinterest_accounts_niche_status", "pinterest_accounts", ["niche_id", "status"]
    )

    # -------------------------------------------------------------- tokens
    op.create_table(
        "pinterest_tokens",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column(
            "pinterest_account_id",
            UUID,
            sa.ForeignKey("pinterest_accounts.id"),
            nullable=False,
        ),
        sa.Column("vault_ref", sa.String(300), nullable=False),
        sa.Column("scopes", sa.String(500), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("access_expires_at", TS, nullable=True),
        sa.Column("refresh_expires_at", TS, nullable=True),
        sa.Column("rotated_at", TS, nullable=True),
        sa.Column("revoked_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_pinterest_tokens_account", "pinterest_tokens", ["pinterest_account_id"], unique=True
    )
    op.create_index(
        "ix_pinterest_tokens_status_expires", "pinterest_tokens", ["status", "access_expires_at"]
    )

    # --------------------------------------------------------------- boards
    op.create_table(
        "pinterest_boards",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column(
            "pinterest_account_id",
            UUID,
            sa.ForeignKey("pinterest_accounts.id"),
            nullable=False,
        ),
        sa.Column("remote_board_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("sync_state", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("last_sync_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_pinterest_boards_account_remote",
        "pinterest_boards",
        ["pinterest_account_id", "remote_board_id"],
        unique=True,
    )
    op.create_index(
        "ix_pinterest_boards_niche_account_status",
        "pinterest_boards",
        ["niche_id", "pinterest_account_id", "status"],
    )
    op.create_index(
        "ix_pinterest_boards_niche_name",
        "pinterest_boards",
        ["niche_id", "pinterest_account_id", "name"],
    )

    # ------------------------------------------------------------- sections
    op.create_table(
        "board_sections",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column(
            "pinterest_account_id",
            UUID,
            sa.ForeignKey("pinterest_accounts.id"),
            nullable=False,
        ),
        sa.Column(
            "pinterest_board_id",
            UUID,
            sa.ForeignKey("pinterest_boards.id"),
            nullable=False,
        ),
        sa.Column("remote_section_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_board_sections_account_remote",
        "board_sections",
        ["pinterest_account_id", "remote_section_id"],
        unique=True,
    )
    op.create_index("ix_board_sections_board_id", "board_sections", ["pinterest_board_id"])

    # ----------------------------------------------------------------- pins
    op.create_table(
        "pinterest_pins",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column(
            "pinterest_account_id",
            UUID,
            sa.ForeignKey("pinterest_accounts.id"),
            nullable=False,
        ),
        sa.Column(
            "pinterest_board_id",
            UUID,
            sa.ForeignKey("pinterest_boards.id"),
            nullable=True,
        ),
        sa.Column("article_id", UUID, nullable=True),
        sa.Column("remote_pin_id", sa.String(100), nullable=True),
        sa.Column("media_ref", sa.String(500), nullable=False, server_default=""),
        sa.Column("pin_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("destination_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("link", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("scheduled_at", TS, nullable=True),
        sa.Column("published_at", TS, nullable=True),
        sa.Column("utms_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_pinterest_pins_account_remote",
        "pinterest_pins",
        ["pinterest_account_id", "remote_pin_id"],
        unique=True,
    )
    op.create_index(
        "uq_pinterest_pins_niche_account_checksum",
        "pinterest_pins",
        ["niche_id", "pinterest_account_id", "checksum"],
        unique=True,
    )
    op.create_index(
        "ix_pinterest_pins_niche_account_status_sched",
        "pinterest_pins",
        ["niche_id", "pinterest_account_id", "status", "scheduled_at"],
    )
    op.create_index("ix_pinterest_pins_published_at", "pinterest_pins", ["published_at"])

    # ------------------------------------------------------------ queue
    op.create_table(
        "pin_queue_items",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column(
            "pinterest_account_id",
            UUID,
            sa.ForeignKey("pinterest_accounts.id"),
            nullable=False,
        ),
        sa.Column(
            "pinterest_pin_id",
            UUID,
            sa.ForeignKey("pinterest_pins.id"),
            nullable=False,
        ),
        sa.Column("state", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("run_at", TS, nullable=False, server_default=NOW),
        sa.Column("completed_at", TS, nullable=True),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("uq_pin_queue_items_pin", "pin_queue_items", ["pinterest_pin_id"], unique=True)
    op.create_index("ix_pin_queue_items_state_run_at", "pin_queue_items", ["state", "run_at"])
    op.create_index(
        "ix_pin_queue_items_niche_account_state",
        "pin_queue_items",
        ["niche_id", "pinterest_account_id", "state"],
    )

    # ------------------------------------------------- attempts
    op.create_table(
        "pin_publish_attempts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column(
            "pinterest_account_id",
            UUID,
            sa.ForeignKey("pinterest_accounts.id"),
            nullable=False,
        ),
        sa.Column(
            "pinterest_pin_id",
            UUID,
            sa.ForeignKey("pinterest_pins.id"),
            nullable=False,
        ),
        sa.Column(
            "pin_queue_item_id",
            UUID,
            sa.ForeignKey("pin_queue_items.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("remote_pin_id", sa.String(100), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_kind", sa.String(30), nullable=False, server_default=""),
        sa.Column("error_detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("started_at", TS, nullable=True),
        sa.Column("completed_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "ix_pin_publish_attempts_pin_attempt",
        "pin_publish_attempts",
        ["pinterest_pin_id", "attempt_no"],
    )
    op.create_index(
        "ix_pin_publish_attempts_niche_account_status",
        "pin_publish_attempts",
        ["niche_id", "pinterest_account_id", "status"],
    )

    # ------------------------------------------------------------ analytics
    op.create_table(
        "pinterest_analytics",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column(
            "pinterest_account_id",
            UUID,
            sa.ForeignKey("pinterest_accounts.id"),
            nullable=False,
        ),
        sa.Column("metric_date", sa.String(10), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outbound_clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagement", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_pinterest_analytics_account_date",
        "pinterest_analytics",
        ["niche_id", "pinterest_account_id", "metric_date"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("pinterest_analytics")
    op.drop_table("pin_publish_attempts")
    op.drop_table("pin_queue_items")
    op.drop_table("pinterest_pins")
    op.drop_table("board_sections")
    op.drop_table("pinterest_boards")
    op.drop_table("pinterest_tokens")
    op.drop_table("pinterest_accounts")
    op.drop_table("pinterest_niches")
