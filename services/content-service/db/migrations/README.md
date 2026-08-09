# content-service — schema migrations

Alembic environment for the content database (`content_db`). The async
environment runs the same migrations against PostgreSQL (production/CI,
`postgresql+asyncpg://...`) and SQLite (migration tests,
`sqlite+aiosqlite:///...`).

## Running

```bash
# From the repository root (venv active):
cd services/content-service
DATABASE_URL=postgresql+asyncpg://atoz:atoz@localhost:5432/content \
  alembic -c db/migrations/alembic.ini upgrade head
```

## Current revision

- `0001_content_initial` — niches, articles, article_versions, categories,
  article_categories, tags, article_tags (ADR-0004).

## Deferred (later milestones)

- `media`, `media_variants`, `article_media` (Phase 6 R2 storage).
- `settings`, `niche_settings` (admin settings milestone).
- PostgreSQL LIST PARTITION BY `niche_id` for catalogs/link tables
  (Database Blueprint §6) — schema is partition-ready (tenancy columns +
  indexes) but partitioning is applied in a later operational migration.
