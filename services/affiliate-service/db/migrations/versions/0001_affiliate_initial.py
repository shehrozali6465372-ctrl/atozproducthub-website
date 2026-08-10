"""affiliate_db tables: niches mirror, networks, merchants, offers, links,
tokens, click attribution, revenue ledgers, webhook logs

Revision ID: 0001
Revises:
Create Date: 2026-08-09

Portable schema (SQLite in tests, PostgreSQL in prod/CI). Primary keys are
UUID v7 strings assigned by the domain layer (ADR-0004). Every business
record carries ``niche_id`` per Database Blueprint §4 — except the global
reference tables (networks, merchants) and the local tenancy mirror
(``affiliate_niches``, ADR-0005: cross-database FKs to content_db ``niches``
are impossible, so affiliate_db keeps its own minimal mirror).

Ledgers (``affiliate_clicks``, ``revenue_transactions``) are append-only:
no update/delete paths exist in the repository layer. ``affiliate_clicks``
references ``revenue_transactions`` through an ORM-level FK only — the
direction is a plain indexed column here because the two tables form a
circular dependency and SQLite cannot ``ALTER TABLE ADD CONSTRAINT``; the
enforced FK is ``revenue_transactions.affiliate_click_id →
affiliate_clicks.id`` (a conversion always points at the click that caused
it, never the reverse).
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
    # ------------------------------------------- local tenancy mirror (ADR-0005)
    op.create_table(
        "affiliate_niches",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("ix_affiliate_niches_slug", "affiliate_niches", ["slug"], unique=True)

    # ------------------------------------------------------ global references
    op.create_table(
        "affiliate_networks",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("feed_type", sa.String(50), nullable=False, server_default="csv"),
        sa.Column("webhook_secret_ref", sa.String(200), nullable=False, server_default=""),
        sa.Column("settings_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("ix_affiliate_networks_code", "affiliate_networks", ["code"], unique=True)

    op.create_table(
        "affiliate_merchants",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "network_id",
            UUID,
            sa.ForeignKey("affiliate_networks.id"),
            nullable=False,
        ),
        sa.Column("remote_merchant_id", sa.String(200), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("commission_terms_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_affiliate_merchants_network_remote",
        "affiliate_merchants",
        ["network_id", "remote_merchant_id"],
        unique=True,
    )
    op.create_index("ix_affiliate_merchants_network_id", "affiliate_merchants", ["network_id"])

    # ------------------------------------------------------ product taxonomy
    op.create_table(
        "product_categories",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("parent_id", UUID, sa.ForeignKey("product_categories.id"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_product_categories_niche_slug", "product_categories", ["niche_id", "slug"], unique=True
    )
    op.create_index(
        "ix_product_categories_niche_parent_id", "product_categories", ["niche_id", "parent_id"]
    )
    op.create_index(
        "ix_product_categories_niche_status", "product_categories", ["niche_id", "status"]
    )

    op.create_table(
        "affiliate_products",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("merchant_id", UUID, sa.ForeignKey("affiliate_merchants.id"), nullable=False),
        sa.Column("sku", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("description_ref", sa.String(500), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("last_feed_at", TS, nullable=True),
        sa.Column("deleted_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_affiliate_products_niche_merchant_sku",
        "affiliate_products",
        ["niche_id", "merchant_id", "sku"],
        unique=True,
    )
    op.create_index(
        "ix_affiliate_products_niche_status_updated",
        "affiliate_products",
        ["niche_id", "status", "updated_at"],
    )
    op.create_index("ix_affiliate_products_merchant_id", "affiliate_products", ["merchant_id"])
    op.create_index("ix_affiliate_products_niche_slug", "affiliate_products", ["niche_id", "slug"])

    op.create_table(
        "product_category_links",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("affiliate_products.id"), nullable=False),
        sa.Column(
            "product_category_id",
            UUID,
            sa.ForeignKey("product_categories.id"),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_pcl_product_category",
        "product_category_links",
        ["product_id", "product_category_id"],
        unique=True,
    )
    op.create_index(
        "ix_pcl_category_product", "product_category_links", ["product_category_id", "product_id"]
    )
    op.create_index("ix_pcl_niche_id", "product_category_links", ["niche_id"])

    # ------------------------------------------------------------------ links
    op.create_table(
        "affiliate_links",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("affiliate_products.id"), nullable=False),
        sa.Column("network_id", UUID, sa.ForeignKey("affiliate_networks.id"), nullable=False),
        sa.Column("network_link_url", sa.Text(), nullable=False),
        sa.Column("default_commission_rate", sa.String(20), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("disclosure_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_affiliate_links_product_network",
        "affiliate_links",
        ["product_id", "network_id"],
        unique=True,
    )
    op.create_index("ix_affiliate_links_niche_status", "affiliate_links", ["niche_id", "status"])

    op.create_table(
        "link_tokens",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("affiliate_link_id", UUID, sa.ForeignKey("affiliate_links.id"), nullable=False),
        sa.Column("token", sa.String(200), nullable=False),
        sa.Column("destination_url", sa.Text(), nullable=False),
        sa.Column("params_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("expires_at", TS, nullable=True),
        sa.Column("revoked_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("uq_link_tokens_token", "link_tokens", ["token"], unique=True)
    op.create_index(
        "ix_link_tokens_affiliate_link_expires", "link_tokens", ["affiliate_link_id", "expires_at"]
    )
    op.create_index("ix_link_tokens_niche_id", "link_tokens", ["niche_id"])

    # -------------------------------------------------------- click attribution
    op.create_table(
        "click_attributions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("pinterest_account_id", UUID, nullable=True),
        sa.Column("pinterest_pin_id", UUID, nullable=True),
        sa.Column("source", sa.String(30), nullable=False, server_default="direct"),
        sa.Column("campaign", sa.String(200), nullable=True),
        sa.Column("utm_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("landing_url", sa.String(1000), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "ix_click_attributions_pin_created",
        "click_attributions",
        ["pinterest_pin_id", "created_at"],
    )
    op.create_index(
        "ix_click_attributions_niche_source_created",
        "click_attributions",
        ["niche_id", "source", "created_at"],
    )

    op.create_table(
        "affiliate_clicks",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("link_token_id", UUID, sa.ForeignKey("link_tokens.id"), nullable=False),
        sa.Column("attribution_id", UUID, sa.ForeignKey("click_attributions.id"), nullable=True),
        # ORM-level FK to revenue_transactions only (see module docstring: the
        # click↔transaction cycle cannot be a DDL constraint on SQLite).
        sa.Column("revenue_transaction_id", UUID, nullable=True),
        sa.Column("clicked_at", TS, nullable=False, server_default=NOW),
        sa.Column("ip_hash", sa.String(128), nullable=True),
        sa.Column("user_agent_hash", sa.String(128), nullable=True),
        sa.Column("referrer", sa.String(1000), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fraud_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_affiliate_clicks_token_clicked_at", "affiliate_clicks", ["link_token_id", "clicked_at"]
    )
    op.create_index(
        "ix_affiliate_clicks_niche_clicked_at", "affiliate_clicks", ["niche_id", "clicked_at"]
    )
    op.create_index(
        "ix_affiliate_clicks_revenue_transaction_id",
        "affiliate_clicks",
        ["revenue_transaction_id"],
    )

    # ---------------------------------------------------------- revenue ledgers
    op.create_table(
        "revenue_transactions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("network_id", UUID, sa.ForeignKey("affiliate_networks.id"), nullable=False),
        sa.Column("affiliate_link_id", UUID, sa.ForeignKey("affiliate_links.id"), nullable=False),
        sa.Column("affiliate_click_id", UUID, sa.ForeignKey("affiliate_clicks.id"), nullable=True),
        sa.Column("network_transaction_id", sa.String(200), nullable=False),
        sa.Column("gross_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("commission_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("occurred_at", TS, nullable=False),
        sa.Column("reconciled_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_revenue_network_transaction",
        "revenue_transactions",
        ["network_id", "network_transaction_id"],
        unique=True,
    )
    op.create_index(
        "ix_revenue_niche_status_occurred",
        "revenue_transactions",
        ["niche_id", "status", "occurred_at"],
    )
    op.create_index("ix_revenue_affiliate_click_id", "revenue_transactions", ["affiliate_click_id"])

    op.create_table(
        "revenue_reconciliations",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("network_id", UUID, sa.ForeignKey("affiliate_networks.id"), nullable=False),
        sa.Column("reported_at", TS, nullable=False),
        sa.Column("expected_total_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actual_total_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delta_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("report_ref", sa.String(500), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_reconciliations_network_date",
        "revenue_reconciliations",
        ["network_id", "reported_at"],
        unique=True,
    )
    op.create_index(
        "ix_reconciliations_niche_status", "revenue_reconciliations", ["niche_id", "status"]
    )

    op.create_table(
        "revenue_summaries",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=False),
        sa.Column("network_id", UUID, sa.ForeignKey("affiliate_networks.id"), nullable=True),
        sa.Column("summary_date", sa.String(10), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sales", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gross_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("commission_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_revenue_summaries_niche_network_date",
        "revenue_summaries",
        ["niche_id", "network_id", "summary_date"],
        unique=True,
    )
    op.create_index("ix_revenue_summaries_summary_date", "revenue_summaries", ["summary_date"])

    # --------------------------------------------------------- webhook ledger
    op.create_table(
        "affiliate_webhook_logs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("niche_id", UUID, nullable=True),
        sa.Column("network_id", UUID, sa.ForeignKey("affiliate_networks.id"), nullable=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("event_id", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="received"),
        sa.Column("payload_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_affiliate_webhook_source_event",
        "affiliate_webhook_logs",
        ["source", "event_id"],
        unique=True,
    )
    op.create_index(
        "ix_affiliate_webhook_logs_network_created",
        "affiliate_webhook_logs",
        ["network_id", "created_at"],
    )


def downgrade() -> None:
    for table in (
        "affiliate_webhook_logs",
        "revenue_summaries",
        "revenue_reconciliations",
        "revenue_transactions",
        "affiliate_clicks",
        "click_attributions",
        "link_tokens",
        "affiliate_links",
        "product_category_links",
        "affiliate_products",
        "product_categories",
        "affiliate_merchants",
        "affiliate_networks",
        "affiliate_niches",
    ):
        op.drop_table(table)
