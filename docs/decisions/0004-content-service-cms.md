# ADR-0004 — Content Service Owns the CMS Business Layer

- **Status:** Accepted
- **Date:** 2026-08-09
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 01-folder-structure.md, 11-database-architecture.md, 12-api-contracts.md, 14-implementation-roadmap.md

## Context

M4 (CMS business layer) is the first business milestone. It must deliver the
content/article domain model, niche and taxonomy integration, content CRUD,
the draft → review → published → archived lifecycle, slug uniqueness, content
versioning, immutable published-content snapshots, author/editor metadata,
PostgreSQL migrations, repository/service/domain layers, admin CMS screens,
public article/category/tag reads, and a full automated test suite — while
keeping the tenancy rules (every content record scoped by `niche_id`), the
Website Architecture Contract, and the M1–M3 foundations intact.

The Database Blueprint and Implementation Roadmap leave the service/module
ownership, status superset, published-snapshot behavior, and tenancy
transport unspecified, so this ADR freezes those decisions.

## Decision

### 1. `services/content-service` owns the content database (`content_db`)

- The content module gets its own schema and its own migration stream
  (Alembic `services/content-service/db/migrations/`), revision `0001`.
- `content_db` contains only business data: niches, articles, versions,
  categories, tags, and the two link tables. No AI OS data lives here; the
  AI OS remains a completely independent external system.
- The service runs its migrations itself in production; CI validates them on
  a fresh PostgreSQL 16 database in the `database` job.

### 2. Status superset (blueprint extension)

- The Implementation Roadmap Phase 6 lifecycle is `draft → review → published
  → archived`. M4 adds `unpublished` (withdraw published content without
  archiving it) and re-publish, so the full legal set is:
  `draft → review → published → archived`, plus `unpublished` and
  `published → published` re-publish. `restore` returns archived content to
  `draft`. All transitions are enforced server-side in the domain state
  machine (`domain/lifecycle.py`) and never inlined in routes or services.

### 3. Immutable published-content snapshot rule

- While an article is `published`, edits never mutate the live snapshot:
  a new immutable version is stored, the article row keeps its
  `content_ref`/`content_checksum` (and slug), and the public API continues
  to serve the unchanged snapshot until an explicit re-publish applies the
  latest version (ADR-0004 §2 `publish: published → published`).
- Content bodies live in object storage (dev: local `var/content`) outside
  the database (Database Blueprint §2.1); versions store `content_ref` +
  SHA-256 `checksum`.

### 4. Tenancy transport and enforcement

- Every content record carries `niche_id` (Database Blueprint §4). All
  repository queries and all mutations are scoped by `niche_id` server-side;
  the public API identifies the niche by slug (`?niche=`), the admin API by
  the mandatory `X-Niche-Id` request header. Cross-niche reads/mutations are
  impossible by construction and tested explicitly.
- Niches themselves are the tenant registry (global, not niche-scoped).

### 5. Partitioning deferred

- The Database Blueprint partition strategy (by niche/date) is deferred until
  real traffic volumes demand it; the schema keeps every table's
  `niche_id` index so partitioning remains a migration without an application
  change.

### 6. Service-local JWT auth boundary

- The content admin API verifies the gateway-issued Bearer JWT locally
  (`content:read` / `content:write` RBAC claims, dev secret default, prod via
  Vault) and never calls the gateway at request time. RBAC claim checks and
  tenancy header validation are FastAPI dependencies shared by every admin
  route.

### 7. UUIDv7 identifiers

- All primary keys are UUIDv7 (`domain/uuids.py`) for time-ordered,
  index-friendly keys that also embed creation time.

## Consequences

- Public readers are never blocked by admin/editor traffic or vice versa;
  public reads are published-only and cacheable.
- Published content is safe against accidental mid-publication edits.
- Admin CMS screens in `apps/admin` are wired to the content-service admin
  API through the typed client when `NEXT_PUBLIC_CONTENT_API_BASE_URL` is
  set, and fall back to mock fixtures otherwise (mock is the CI/default
  build mode).
- No AI functionality was added: content is created/edited by editors; all
  intelligence stays in the AI OS and enters the website only through the AI
  OS Bridge.

## Contract compliance

- **No AI duplication:** the content service contains no research, writing,
  image, SEO-generation, learning, memory, prompt, router, model, or LLM
  code; the no-AI CI guard scans it like every tree.
- **Business layer only:** the service implements business use cases only;
  the AI OS remains external and is never called directly by M4 code.
- **Tenancy:** every business object is niche-scoped; no cross-niche data
  leakage is possible, and isolation is covered by repository, service, and
  HTTP-level tests.
