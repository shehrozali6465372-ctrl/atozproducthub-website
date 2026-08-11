# ADR-0007 — SEO Service Owns the SEO & Discovery Business Layer

- **Status:** Accepted
- **Date:** 2026-08-11
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 01-folder-structure.md, 11-database-architecture.md, 12-api-contracts.md, 14-implementation-roadmap.md

## Context

M7 (SEO & discovery layer) is the findability milestone. It must deliver
applied SEO metadata, canonical URL policy and duplicate-URL prevention,
robots rules that never block Pinterestbot or its image proxy, JSON-LD and
Open Graph output, sharded sitemaps at million-URL scale, Google/Bing
crawl-report boundaries, niche-scoped Typesense search, and event-driven
indexing/de-indexing — all inside the Website Architecture Contract, with
strict niche tenancy and zero AI functionality.

The Database Blueprint (§5.14) and API Contracts define the `url_registry`,
`seo_metadata`, `sitemap_shards`, `seo_crawl_reports`, and
`seo_health_checks` tables and the event flow, but leave service ownership,
tenancy transport, search-index storage, sitemap serving, robots policy, and
the AI OS boundary unspecified, so this ADR freezes those decisions.

## Decision

### 1. `services/seo-service` owns the SEO database (`seo_db`)

- The SEO module gets its own Alembic migration stream
  (`services/seo-service/db/migrations/`), revision `0001`, with its own
  version table (`alembic_version_seo`) so the content, affiliate, Pinterest,
  and SEO streams apply to the same physical database without interfering
  (same policy as ADR-0005/0006).
- `seo_db` holds only business data: local niche mirror, URL registry,
  applied metadata, sitemap shard state, crawl reports, and health checks.
  Search index state (Typesense) is derived from domain events and is never
  stored in PostgreSQL; PostgreSQL remains the source of truth.
- CI validates the SEO migration stream against the same fresh PostgreSQL 16
  used by the other services, including downgrade/re-upgrade.

### 2. Local tenancy mirror and slug-based public reads

- Every `seo_db` business record carries `niche_id` (Database Blueprint §4).
- Cross-database foreign keys to `content_db.niches` are impossible, so
  `seo_db` keeps its own minimal `seo_niches` mirror (slug + name + status),
  read-only inside the service (same policy as ADR-0004/0005/0006).
- Public routes identify the niche by slug (never by id); admin routes use
  the mandatory `X-Niche-Id` header and JWT RBAC (`seo:read`/`seo:write`).
- URL slugs are niche-global: the service rejects the same slug claimed by
  two different entities in one niche (409 `DUPLICATE`), in addition to the
  database-level `UNIQUE (niche_id, path)`.

### 3. Search index boundary (Typesense, lexical only)

- `seo-service` exposes a `SearchIndex` ABC. The production implementation
  is a Typesense client (collection `seo_content`, configured via
  `TYPESENSE_API_BASE`/`TYPESENSE_API_KEY`); an in-memory implementation is
  used for development and tests so the service and CI run without a live
  Typesense instance.
- Indexing is event-driven: `content:published.v1` → index,
  `content:updated.v1` → re-index, `content:unpublished.v1` → remove,
  `product:ingested.v1` → index, `product:removed.v1` → remove. Every
  document carries `niche_id`; every query is niche-scoped server-side.
- No embeddings, vectors, or semantic ranking exist in the business layer —
  that would be AI OS intelligence.

### 4. Sitemap and robots serving

- Sitemaps are sharded (`sitemap_max_urls` URLs per shard) with one index
  per group (`articles`, `categories`, `tags`, `products`, `landing`,
  `collections`). Only active public URLs are ever included.
- Shards and indexes are rendered as XML and served by the service
  (`/api/v1/public/seo/sitemaps/{group}-index.xml` and `{group}-{n}.xml`).
  The Next.js site proxies them at `/sitemap.xml`, `/robots.txt`, and
  `/sitemaps/{group}-{n}.xml` with strict filename validation.
- robots.txt allows Googlebot, Bingbot, and Pinterestbot (and its image
  proxy); admin, API, search, internal asset, and private paths are blocked.

### 5. AI OS boundary

- The SEO service contains zero AI generation: no model SDKs, no prompts,
  no embeddings, no LLM calls. SEO metadata intelligence arrives only via
  the existing `Website → AI OS Bridge → AI OS` path
  (`libs/contracts/aios/seo-metadata.schema.json`); the service validates,
  stores, and serves the applied business output.
- Google Search Console and Bing Webmaster credentials are server-side
  boundaries only (`gsc_service_account_ref`, `bing_api_key_ref` Vault
  refs); endpoints are mocked in tests and never exposed to the frontend.

## Consequences

- The SEO module follows the M4/M5/M6 service conventions exactly: domain
  entities, niche-scoped repositories, a `SeoUnitOfWork`, a `SeoService`
  facade, public/admin/webhook routes, RFC7807 errors, and a full test
  suite (sitemap XML validation, JSON-LD, robots, search isolation, URL
  registry duplicates, migrations, and HTTP-level tenancy).
- The website UI applies SEO metadata and JSON-LD produced by the service
  through typed client methods (`api.seo.getMetadata`, `api.seo.search`,
  `api.seo.getRobots`, `api.seo.getSitemap`) and proxies robots/sitemaps at
  the site origin; no intelligence is generated in the frontend.
- Live GSC/Bing credential provisioning, the `AIOS.SEO.Metadata` gate,
  Lighthouse CI budgets, and crawl-report ingestion from real Google/Bing
  accounts remain follow-ups (production operator actions).

## Contract compliance

- **No AI duplication:** the SEO service contains no intelligence; the
  no-AI CI guard scans it and `pip-audit` blocks AI SDKs.
- **Business layer only:** the service implements business use cases only
  (URL policy, metadata application, sitemaps, robots, crawl reports,
  search indexing); metadata intelligence belongs to the AI OS and enters
  the website only through the AI OS Bridge.
- **Tenancy:** every `seo_db` business record carries `niche_id`; cross-niche
  search/metadata leakage is impossible and covered by repository, service,
  and HTTP-level tests.
- **Secrets:** GSC/Bing credentials live behind Vault references; dev
  defaults are placeholders that must be provisioned in production.
