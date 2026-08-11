# seo-service

SEO metadata application, canonical URL policy, robots rules, JSON-LD,
sharded sitemaps, crawl-report boundaries, and niche-scoped Typesense
search — M7 SEO & Discovery layer (ADR-0007).

- **Owner:** @atoz/seo
- **Status:** M7 complete (v0.7.0) — business layer only.
- **Database:** owns `seo_db` tables (own Alembic stream, version table
  `alembic_version_seo`) — `seo_niches`, `url_registry`, `seo_metadata`,
  `sitemap_shards`, `seo_crawl_reports`, `seo_health_checks`.
- **Search index:** Typesense (lexical only, `SearchIndex` ABC with an
  in-memory implementation for dev/tests). PostgreSQL stays the source of
  truth; indexing is event-driven from content/product domain events.
- **Endpoints:**
  - Public: `/api/v1/public/seo/meta`, `/api/v1/public/seo/robots`,
    `/api/v1/public/seo/sitemaps/{group}-index.xml` and `{group}-{n}.xml`,
    `/api/v1/public/search` — all niche-scoped by slug.
  - Admin: `/api/v1/admin/*` — JWT RBAC `seo:read`/`seo:write` +
    mandatory `X-Niche-Id` header.
  - Webhooks: `/webhooks/v1/seo/events` — HMAC `X-Event-Signature`
    verified event ingestion (content/product lifecycle events).
  - Shared: `/health`, `/ready`, `/metrics` (backend-core factory).
- **Migrations:** `db/migrations/` — `DATABASE_URL`-driven; validated
  against fresh PostgreSQL 16 in CI.
- **AI OS boundary:** this service never contacts the AI OS directly and
  contains zero AI logic. SEO metadata intelligence arrives only through
  `services/aios-bridge/` + `libs/contracts/aios/seo-metadata.schema.json`;
  the service validates, stores, and serves the applied business output.
