# seo-service — schema migrations

Alembic environment for the SEO database (`seo_db`). The async environment
runs the same migrations against PostgreSQL (production/CI,
`postgresql+asyncpg://...`) and SQLite (migration tests,
`sqlite+aiosqlite:///...`).

## Running

```bash
# From the repository root (venv active):
cd services/seo-service
DATABASE_URL=postgresql+asyncpg://atoz:atoz@localhost:5432/atoz \
  alembic -c db/migrations/alembic.ini upgrade head
```

## Current revision

- `0001_seo_initial` — seo_niches (tenancy mirror, ADR-0007),
  url_registry, seo_metadata, sitemap_shards, seo_crawl_reports,
  seo_health_checks.

## Notes

- Strict niche tenancy (Database Blueprint §4): every SEO record carries
  `niche_id`; URL paths are unique per niche (duplicate-URL prevention).
- Search index state (Typesense) is derived from domain events and never
  stored here; PostgreSQL remains the source of truth (blueprint §10).
- No AI data lives here: metadata intelligence arrives via the AI OS
  Bridge and is stored as applied business output.

## Deferred (later milestones)

- PostgreSQL LIST PARTITION BY `niche_id` for high-volume URL sets if a
  niche exceeds millions of URLs (schema is partition-ready: tenancy
  columns + composite indexes).
