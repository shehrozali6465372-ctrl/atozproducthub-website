"""Bootstrap the ten production niches supported by AtoZ Product Hub."""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NICHES = (
    ("7b7e9c6a-3f8d-4f6b-9a21-5c8d2e4f7a10", "Kitchen", "kitchen"),
    ("1a2b3c4d-5e6f-47a8-9b10-2c3d4e5f6a70", "Beauty", "beauty"),
    ("2b3c4d5e-6f70-48a9-9b21-3d4e5f6a7b81", "Fitness", "fitness"),
    ("3c4d5e6f-7081-49ba-9c32-4e5f6a7b8c92", "Fashion", "fashion"),
    ("4d5e6f70-8192-4acb-9d43-5f6a7b8c9da3", "Home", "home"),
    ("5e6f7081-92a3-4bdc-9e54-6a7b8c9daeb4", "Electronics", "electronics"),
    ("6f708192-a3b4-4ced-9f65-7b8c9daebfc5", "Travel", "travel"),
    ("708192a3-b4c5-4def-a076-8c9daebfc0d6", "Pets", "pets"),
    ("8192a3b4-c5d6-4ef0-a187-9daebfc0d1e7", "Automotive", "automotive"),
    ("92a3b4c5-d6e7-4f01-a298-aebfc0d1e2f8", "Garden", "garden"),
)

def upgrade() -> None:
    niches = sa.table("niches", sa.column("id", sa.String(36)), sa.column("name", sa.String(200)), sa.column("slug", sa.String(200)), sa.column("status", sa.String(20)), sa.column("default_currency", sa.String(3)))
    bind = op.get_bind()
    for niche_id, name, slug in NICHES:
        row = bind.execute(sa.select(niches.c.id).where(niches.c.slug == slug)).first()
        if row is None:
            op.bulk_insert(niches, [{"id": niche_id, "name": name, "slug": slug, "status": "active", "default_currency": "USD"}])
        else:
            bind.execute(niches.update().where(niches.c.slug == slug).values(status="active"))

def downgrade() -> None:
    pass
