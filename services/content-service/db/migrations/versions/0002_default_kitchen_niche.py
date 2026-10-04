"""Bootstrap the default website niche used by the public web client.

The website contract defaults to the kitchen niche. A fresh production
database must therefore contain an active niche before public reads are
enabled. This migration is idempotent at the migration level and creates
only the tenant registry entry; content remains empty until provisioned.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NICHE_ID = "7b7e9c6a-3f8d-4f6b-9a21-5c8d2e4f7a10"


def upgrade() -> None:
    niches = sa.table(
        "niches",
        sa.column("id", sa.String(36)),
        sa.column("name", sa.String(200)),
        sa.column("slug", sa.String(200)),
        sa.column("status", sa.String(20)),
        sa.column("default_currency", sa.String(3)),
    )
    bind = op.get_bind()
    exists = bind.execute(
        sa.select(niches.c.id).where(niches.c.slug == "kitchen")
    ).first()
    if exists is None:
        op.bulk_insert(
            niches,
            [
                {
                    "id": NICHE_ID,
                    "name": "Kitchen",
                    "slug": "kitchen",
                    "status": "active",
                    "default_currency": "USD",
                }
            ],
        )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM niches WHERE id = :id AND slug = :slug").bindparams(
            id=NICHE_ID, slug="kitchen"
        )
    )
