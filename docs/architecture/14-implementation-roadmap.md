# 14 — Implementation Roadmap (Master Implementation Plan)

**Status:** Permanent roadmap — the plan for Task 9 (actual development)
**Version:** 1.0
**Compliance:** Must satisfy every planning document: [Architecture](README.md), [Website Contract](09-website-architecture-contract.md), [Folder Blueprint](01-folder-structure.md), [Technology Stack](10-technology-stack.md), [Database Blueprint](11-database-architecture.md), [API Contracts](12-api-contracts.md), [UI/UX Design System](13-ui-ux-design-system.md)

This document is the **master implementation plan**: phases, module details, dependency-ordered sequence, milestones, and Definitions of Done. No production code is written here — this roadmap is executed in Task 9.

---

## 1. Roadmap principles

1. **Nothing is built before its dependency.** Each phase has a hard dependency list; a phase starts only when its dependencies' DoDs pass.
2. **Docs before code, always.** No phase begins before its scope is confirmed against the planning documents.
3. **Vertical slices beat horizontal sprawl.** Where possible, phases deliver working end-to-end slices (UI → API → service → database → event).
4. **The AI OS is an external dependency.** Website work never blocks on the AI OS; bridge contracts are stubbed with mocks until the real AI OS is connected, and real integration is gated per phase.
5. **Security and tenancy are non-negotiable from Phase 1.** Tenancy checks, secrets hygiene, and no-AI-duplication checks run in CI from the first commit.
6. **Every phase ends at a milestone with a Definition of Done.** No phase is "almost done."

## 2. Phase and module overview

| Phase | Name | Complexity | Risk | Depends on | Milestone |
|-------|------|-----------|------|------------|-----------|
| 1 | Repository Setup | S | Low | — | M1 |
| 2 | Frontend Foundation | M | Medium | 1 | M2 |
| 3 | Backend Foundation | L | Medium | 1 | M2 |
| 4 | Database | L | High | 1, 3 | M2 |
| 5 | Authentication | L | High | 3, 4 | M3 |
| 6 | Website CMS | XL | High | 2, 3, 4, 5 | M3 |
| 7 | Affiliate Engine | XL | High | 3, 4, 5, 6 | M4 |
| 8 | Pinterest Business Layer | XL | High | 3, 4, 6, 7 | M5 |
| 9 | SEO Layer | L | Medium | 2, 3, 4, 6, 7 | M6 |
| 10 | Analytics | XL | High | 2, 3, 4, 6, 7, 8 | M6 |
| 11 | Admin Dashboard | XL | Medium | 5, 6, 7, 8, 9, 10 | M7 |
| 12 | Automation | M | Medium | 4, 5, 6, 7, 8, 9, 10, 11 | M7 |
| 13 | Production Deployment | L | High | 1–12 | M8 |

Complexity scale: S = small (days), M = medium (1–2 weeks), L = large (2–4 weeks), XL = extra large (4–8 weeks). Effort is indicative, not committed.

---

## 3. Implementation order

**Dependency-ordered sequence:**

```
Phase 1
   ├── Phase 2 (Frontend Foundation) ── parallel track ──┐
   └── Phase 3 (Backend Foundation) ── parallel track ──┴── Phase 4 (Database)
                                                                  │
   Phase 5 (Authentication) ◄── Phase 4
   Phase 6 (Website CMS) ◄── 2, 3, 4, 5
   Phase 7 (Affiliate Engine) ◄── 3, 4, 5, 6
   Phase 8 (Pinterest Business Layer) ◄── 3, 4, 6, 7
   Phase 9 (SEO Layer) ◄── 2, 3, 4, 6, 7          ── parallel track ──┐
   Phase 10 (Analytics) ◄── 2, 3, 4, 6, 7, 8      ── parallel track ──┴── Phase 11 (Admin Dashboard)
   Phase 12 (Automation) ◄── 4, 5, 6, 7, 8, 9, 10, 11
   Phase 13 (Production Deployment) ◄── 1–12
```

**Ordering rules:**
1. Phase 1 gates everything.
2. Phases 2 and 3 run in parallel after Phase 1 (frontend and backend tracks).
3. Phase 4 starts once Phase 3's service skeletons exist to host migrations.
4. Phases 9 and 10 may overlap once their producers (6, 7, 8) emit events.
5. Phase 11 waits for read models from 6–10; Phase 12 waits for 11's control surfaces.
6. Phase 13 is last and only after all DoDs pass.

**AI OS integration gates (external dependency):**

| Phase | Bridge contract exercised | Gate |
|-------|---------------------------|------|
| 3 | `AIOS.Heartbeat`, stubbed adapters | Mock AI OS in dev |
| 6 | `AIOS.Content.Intake`, `AIOS.Job.Request/Status` | Real AI OS connected at M3 |
| 8 | `AIOS.Pinterest.Assets` | Real AI OS at M5 |
| 9 | `AIOS.SEO.Metadata` | Real AI OS at M6 |
| 10 | `AIOS.Analytics.Insights` | Real AI OS at M6 |

---

## 4. Phase definitions and module details

For every phase: Goal, Scope, Deliverables, Dependencies, Complexity, Risk, Success Criteria + module breakdown (Files, Folders, Dependencies, Database tables used, API contracts used, Future integrations, Testing requirements).

### Phase 1 — Repository Setup

- **Goal:** Stand up the monorepo exactly per the Folder Blueprint with CI, tooling, and dev environment that boot on a clean machine.
- **Scope:** Create all blueprint folders with README stubs; root tooling (`package.json`, `pyproject.toml`, `Makefile`, `.editorconfig`, `.env.example`); GitHub Actions baseline (lint, format, contract validation); Docker Compose for local dev; `libs/contracts` + `libs/domain-core` initial structure; ADR process started; tenancy/no-AI CI checks wired.
- **Deliverables:** scaffolded monorepo, green CI, `make setup` boots Postgres + Redis + empty services, contract file layout, contributing docs synced.
- **Dependencies:** Planning documents only (Tasks 1–7).
- **Estimated Complexity:** S.
- **Risk Level:** Low.
- **Success Criteria:** clean-machine setup succeeds; CI runs lint + format + contract schema validation + no-AI dependency scan; `docker compose up` is healthy.

| Module detail | |
|---|---|
| **Files** | `package.json`, `pyproject.toml`, `Makefile`, `.editorconfig`, `.env.example`, `.gitignore`, `.github/workflows/*.yml`, `docker-compose.yml`, root READMEs |
| **Folders** | All folders from Folder Blueprint §3: `apps/`, `services/`, `libs/`, `config/`, `infra/`, `assets/`, `pipelines/`, `tests/`, `tools/`, `docs/` |
| **Dependencies** | None (code-wise) |
| **Database tables used** | None |
| **API contracts used** | None implemented; contract directories created |
| **Future integrations** | Every later phase |
| **Testing requirements** | CI baseline: lint, format, contract schema validation, secret scan, no-AI dependency scan, compose smoke |

### Phase 2 — Frontend Foundation

- **Goal:** Both Next.js apps (web + admin) scaffolded with the complete visual foundation from the UI/UX Design System.
- **Scope:** `apps/web` + `apps/admin`; design tokens (color, type, spacing, dark mode); layout system (header, footer, nav, sidebar, breadcrumbs); core components (buttons, cards, forms, tables, notifications, search, pagination, filters); responsive behavior at 4 breakpoints; accessibility baseline; Lighthouse CI budgets; typed API client wired to `libs/contracts` (mock data).
- **Deliverables:** two apps render placeholder pages with the design system; dark mode; a11y checks pass; CWV budgets enforced in CI; component test suite.
- **Dependencies:** Phase 1; UI/UX Design System; API Contracts (Public Read for client types).
- **Estimated Complexity:** M.
- **Risk Level:** Medium (design consistency across surfaces).
- **Success Criteria:** pages pass axe checks; render correctly at 360/768/1024/1440; Lighthouse budgets in CI; design tokens match §3–§8 of the design system.

| Module detail | |
|---|---|
| **Files** | `apps/web/src/app/*`, `apps/web/src/components/*`, `apps/web/src/lib/api-client.ts`, `apps/web/src/styles/*`, `apps/admin/*` (same shape), `next.config.*`, `package.json`, tests |
| **Folders** | `apps/web/`, `apps/admin/`, `libs/contracts/` (client types), `assets/` (brand) |
| **Dependencies** | Phase 1; contracts schemas |
| **Database tables used** | None (mock data) |
| **API contracts used** | Public Read API (client consumption, mocked) |
| **Future integrations** | Mobile app (reuses tokens/components), newsletters |
| **Testing requirements** | Component tests, a11y tests (axe), responsive visual tests, Lighthouse CI |

### Phase 3 — Backend Foundation

- **Goal:** API gateway and all service skeletons running with config, Docker, observability, and the AI OS Bridge skeleton.
- **Scope:** `apps/api` gateway (routing, auth middleware stubs, webhook receiver skeletons); skeletons for content/pinterest/affiliate/seo/analytics/admin services + `services/aios-bridge` (health, `AIOS.Heartbeat`, contract adapters stubbed with a mock AI OS); `libs/contracts` + `libs/domain-core` implemented (OpenAPI/AsyncAPI packages, codegen); Dockerfiles; `config/dev|staging|prod`; Vault dev setup; OpenTelemetry + structured logging.
- **Deliverables:** gateway and every service boot with `/health`; contract packages build and validate; Docker Compose runs the full stack; traces/logs flow; CI builds images.
- **Dependencies:** Phase 1; Technology Stack; API Contracts (bridge contracts).
- **Estimated Complexity:** L.
- **Risk Level:** Medium.
- **Success Criteria:** `docker compose up` healthy for all containers; contract validation tests pass; `AIOS.Heartbeat` works against the mock AI OS; OTel spans visible in dev.

| Module detail | |
|---|---|
| **Files** | `apps/api/src/*`, `services/*/src/{domain,application,adapters,api}`, per-service `pyproject.toml` + `Dockerfile`, `libs/contracts/*`, `tools/codegen/*`, `infra/docker/*`, `config/*/env.template` |
| **Folders** | `apps/api/`, `services/*/`, `libs/contracts/`, `libs/domain-core/`, `infra/docker/`, `infra/observability/`, `infra/secrets/`, `config/`, `tools/` |
| **Dependencies** | Phase 1 |
| **Database tables used** | None yet (health endpoints only) |
| **API contracts used** | Internal service contracts; `AIOS.Heartbeat`; stubbed `AIOS.Job.Request/Status` |
| **Future integrations** | All phases 5–13 |
| **Testing requirements** | Unit tests per service, contract schema tests, compose smoke tests, OTel trace assertions |

### Phase 4 — Database

- **Goal:** Production-grade database foundation per the Database Blueprint, with tenancy isolation enforced by schema.
- **Scope:** `infra/db` (init, partitioning, backup scripts); per-service migrations for **all** blueprint §5 tables; PgBouncer pooling; Redis (cache/queues); ClickHouse schema (`analytics_events`); Typesense collections (empty, per-niche); R2 buckets; Alembic tooling; migration CI gate; backup (nightly + WAL) and automated restore drill in staging.
- **Deliverables:** every table from the blueprint created with constraints (uniques, FKs, tenancy columns); partitions and local indexes verified; backups configured; restore drill passes.
- **Dependencies:** Phase 1; Phase 3 (skeletons to host migrations); Database Blueprint.
- **Estimated Complexity:** L.
- **Risk Level:** High (data correctness).
- **Success Criteria:** clean migration from empty → prod-like succeeds; tenancy constraint tests pass (no cross-niche FKs); partition pruning verified for hot queries; restore drill passes in staging.

| Module detail | |
|---|---|
| **Files** | `services/*/db/migrations/*`, `infra/db/*`, Alembic configs, `infra/iac/db*`, `config/*/db/*`, `infra/iac/clickhouse*`, `infra/iac/search*` |
| **Folders** | `services/*/db/migrations/`, `infra/db/`, `infra/iac/` |
| **Dependencies** | Phase 1, Phase 3 |
| **Database tables used** | ALL blueprint §5 tables (niches, pinterest_accounts/tokens/boards/pins, articles/versions, categories/tags, affiliate networks/merchants/products/categories/links, link_tokens/clicks/attributions, revenue, SEO, traffic, analytics read models, users/roles/permissions, api_keys, automation/scheduler/queue, logs/audit, notifications, media, settings, aios_job_records) |
| **API contracts used** | None (schema-level) |
| **Future integrations** | Archive jobs (Phase 12), warehouse growth (Phase 10) |
| **Testing requirements** | Migration CI gate, tenancy constraint tests, unique-constraint tests, partition-pruning tests, backup/restore drill |

### Phase 5 — Authentication

- **Goal:** Identity foundation: OIDC login, MFA, RBAC, API keys, audit trail.
- **Scope:** Identity tables and service logic (admin users, roles, permissions, user roles, api keys, consent); OIDC integration (JWT + MFA); RBAC middleware in the gateway; `audit_logs` writes on every admin action; admin login page; session/refresh handling; API keys for automation.
- **Deliverables:** admin login end-to-end; RBAC enforced on admin API; MFA required; audit immutability; API-key lifecycle (issue, rotate, revoke).
- **Dependencies:** Phase 3 (gateway), Phase 4 (identity tables).
- **Estimated Complexity:** L.
- **Risk Level:** High (security).
- **Success Criteria:** authN/Z matrix tests pass; MFA enforced; audit log append-only verified; no secrets in logs; pen-test-ready.

| Module detail | |
|---|---|
| **Files** | `services/admin-service/src/identity*`, gateway middleware, `apps/admin/src/app/login`, `libs/contracts/admin/*` |
| **Folders** | `services/admin-service/`, `apps/admin/`, `libs/contracts/admin/` |
| **Dependencies** | Phase 3, Phase 4 |
| **Database tables used** | `admin_users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `api_keys`, `consent_records`, `audit_logs` |
| **API contracts used** | Admin API (auth endpoints), OIDC discovery, `Idempotency-Key` support |
| **Future integrations** | Additional IdPs, reader accounts (mobile phase), SSO |
| **Testing requirements** | AuthN/Z matrix tests, MFA e2e, audit immutability tests, token rotation tests, security scan |

### Phase 6 — Website CMS

- **Goal:** The content pipeline: intake → validate → store → publish → serve article/category/tag pages.
- **Scope:** `content-service` (articles, versions, categories, tags, media); R2 media storage; article/category/tag pages in `apps/web`; admin review/approve/publish flow; first **real** AI OS integration (`AIOS.Content.Intake` via Bridge); content events emitted; basic search-index sync.
- **Deliverables:** end-to-end publish flow; article page serves from DB; media upload/variants; AI OS intake path (mock → real AI OS at M3); content events consumed by search/analytics stubs.
- **Dependencies:** Phases 2, 3, 4, 5; API Contracts (content + bridge).
- **Estimated Complexity:** XL.
- **Risk Level:** High (content correctness + first AI OS integration).
- **Success Criteria:** publish → render e2e passes; intake dedupe by checksum works; versioning immutable; events flow; article page passes CWV budgets.

| Module detail | |
|---|---|
| **Files** | `services/content-service/src/*`, content migrations, `apps/web` article/category/tag pages, `apps/admin` content screens, `libs/contracts/content/*` |
| **Folders** | `services/content-service/`, `apps/web/src/app/{articles,categories,tags}/`, `apps/admin` content, `assets/templates/` |
| **Dependencies** | Phases 2, 3, 4, 5 |
| **Database tables used** | `niches`, `articles`, `article_versions`, `categories`, `article_categories`, `tags`, `article_tags`, `media`, `media_variants`, `article_media`, `settings`, `niche_settings` |
| **API contracts used** | Public Read (articles), Admin API (content), `AIOS.Content.Intake`, `AIOS.Job.Request/Status`, events `content:*` |
| **Future integrations** | Newsletter digests, mobile content reads, related-content module |
| **Testing requirements** | Publish e2e, intake dedupe tests, version immutability tests, media validation, event contract tests, page CWV checks |

### Phase 7 — Affiliate Engine

- **Status:** ✅ Complete (M5, v0.5.0 — ADR-0005). First network webhook
  ingestion, signed redirector, click/conversion ledgers, commission
  lifecycle, disclosure enforcement, and admin/public affiliate UI are
  implemented and tested. Follow-ups: outbound network feed adapters and
  production reconciliation job automation.
- **Goal:** The monetization core: product catalog, link tokens, click attribution, and revenue ledger.
- **Scope:** `affiliate-service` (networks, merchants, products, product categories, links, tokens, clicks, attributions, revenue, reconciliation); first network adapter; `/go/{token}` redirector; product and collection pages in `apps/web`; disclosure UI enforced by templates; click/revenue events.
- **Deliverables:** product ingest from one network; redirect with attribution + dedupe; commission webhook processing; product pages with disclosure; revenue summaries; reconciliation job.
- **Dependencies:** Phases 3, 4, 5, 6 (article cards link to products).
- **Estimated Complexity:** XL.
- **Risk Level:** High (money correctness, fraud).
- **Success Criteria:** click dedupe ≥ 99.9%; reconciliation matches network reports; disclosure enforced on every monetized surface; revenue events flow.

| Module detail | |
|---|---|
| **Files** | `services/affiliate-service/src/*`, network adapters, redirect handler, `apps/web` product/collection pages, `libs/contracts/affiliate/*` |
| **Folders** | `services/affiliate-service/`, `apps/web/src/app/{products,go,collections}/`, `libs/contracts/affiliate/` |
| **Dependencies** | Phases 3, 4, 5, 6 |
| **Database tables used** | `affiliate_networks`, `affiliate_merchants`, `affiliate_products`, `product_categories`, `product_category_links`, `affiliate_links`, `link_tokens`, `affiliate_clicks`, `click_attributions`, `revenue_transactions`, `revenue_reconciliations`, `revenue_summaries` |
| **API contracts used** | Public Read (products), Admin API (catalog), webhook `network.conversion`, events `affiliate:click`, `revenue:attributed` |
| **Future integrations** | More networks, payout providers, reviews/ratings |
| **Testing requirements** | Attribution/dedupe tests, fraud tests, reconciliation e2e, disclosure compliance tests, click-ledger load tests |

### Phase 8 — Pinterest Business Layer

- **Status:** ✅ Complete (M6, v0.6.0 — ADR-0006). Per-account Pinterest
  business layer: OAuth connect (PKCE + state/CSRF), Vault-bound token
  records, board/section sync, queue-based pin publishing with idempotency +
  retry, per-account org_read/org_write rate limits, publishing-attempt and
  analytics records, admin + read-only public APIs, and Pinterest admin /
  landing UI are implemented and tested. Follow-ups: live Pinterest app
  credential provisioning, `AIOS.Pinterest.Assets` gate, Pinterest Tag, and
  scheduler integration.
- **Goal:** Pinterest operations at scale: 10+ accounts, boards, pins, scheduling, landing pages — with strict per-account isolation.
- **Scope:** `pinterest-service` (accounts, token vault refs, boards, pin ledger, pin queue, rate-limit budgets); Pinterest API v5 adapter; scheduler integration; `AIOS.Pinterest.Assets` requests; Pinterest Tag; landing pages in `apps/web`; attribution events.
- **Deliverables:** account CRUD per niche; board sync; pin schedule + publish via Pinterest API; rate-limit safety; landing pages live; `pin:*` events; Pinterest Tag firing.
- **Dependencies:** Phases 3, 4, 6 (landing content), 7 (attribution), 5 (auth for admin control).
- **Estimated Complexity:** XL.
- **Risk Level:** High (external API, rate limits, account isolation).
- **Success Criteria:** 10 accounts configured with zero cross-account data leakage (tests); 1,000+ pins scheduled/published; one account's throttle never affects others; attribution recorded for every published pin.

| Module detail | |
|---|---|
| **Files** | `services/pinterest-service/src/*`, Pinterest adapter, queue workers, `apps/web` landing pages, `libs/contracts/pinterest/*` |
| **Folders** | `services/pinterest-service/`, `apps/web/src/app/pin-landing/*`, `libs/contracts/pinterest/` |
| **Dependencies** | Phases 3, 4, 5, 6, 7 |
| **Database tables used** | `pinterest_accounts`, `pinterest_tokens`, `pinterest_boards`, `pinterest_pins`, `pin_queue_items`, `click_attributions` (pin source) |
| **API contracts used** | Pinterest API v5, `AIOS.Pinterest.Assets`, `AIOS.Job.Request/Status`, webhooks `pinterest.*`, events `pin:*` |
| **Future integrations** | Additional visual channels (if adopted) |
| **Testing requirements** | Account-isolation tests, rate-limit tests, queue retry/failure tests, landing-page e2e, Pinterest sandbox integration tests |

### Phase 9 — SEO Layer

- **Status:** ✅ Complete (M7, v0.7.0 — ADR-0007). Applied SEO metadata and
  canonical URL policy (duplicate-URL prevention), robots rules that never
  block Pinterestbot or its image proxy, JSON-LD/Open Graph output, sharded
  sitemaps + indexes, GSC/Bing crawl-report boundaries, niche-scoped
  Typesense search with event-driven indexing, site-origin robots/sitemap
  proxies, and a Lighthouse Core Web Vitals + SEO CI gate are implemented
  and tested. Follow-ups: live GSC/Bing credential provisioning, the
  `AIOS.SEO.Metadata` gate (external AI OS), hreflang, and crawl-API
  expansions.
- **Goal:** SEO production: metadata application, sharded sitemaps, structured data, crawl health.
- **Scope:** `seo-service` (`url_registry`, `seo_metadata`, `sitemap_shards`, `seo_crawl_reports`, `seo_health_checks`); sitemap sharding jobs; JSON-LD rendering on article/product/collection pages; GSC + Bing ingestion; `AIOS.SEO.Metadata` integration; per-niche robots; Lighthouse CI budgets active.
- **Deliverables:** sharded sitemaps served from CDN; JSON-LD validated; URL policy + redirects; GSC data in dashboards; SEO health reports.
- **Dependencies:** Phases 2, 3, 4, 6 (articles), 7 (products).
- **Estimated Complexity:** L.
- **Risk Level:** Medium.
- **Success Criteria:** sitemaps valid for 1M+ URLs (sharded); structured-data validator clean; CWV budgets pass in CI; redirects correct.

| Module detail | |
|---|---|
| **Files** | `services/seo-service/src/*`, sitemap jobs, `apps/web` metadata components, `libs/contracts/seo/*` |
| **Folders** | `services/seo-service/`, `libs/contracts/seo/`, `infra/observability/` (CWV dashboards) |
| **Dependencies** | Phases 2, 3, 4, 6, 7 |
| **Database tables used** | `url_registry`, `seo_metadata`, `sitemap_shards`, `seo_crawl_reports`, `seo_health_checks` |
| **API contracts used** | GSC + Bing APIs, `AIOS.SEO.Metadata`, event `seo:sitemap-rebuilt` |
| **Future integrations** | hreflang (multilingual), site search, crawl-API expansions |
| **Testing requirements** | Sitemap validation tests, JSON-LD schema tests, redirect tests, crawl-report ingestion tests |

### Phase 10 — Analytics

- **Status:** ✅ Complete (M8, v0.8.0 — ADR-0008). First-party collector
  (single + batch, slug tenancy, `event_id` idempotency, append-only ledger,
  sensitive-trait guard), HMAC-verified domain-event webhook, daily/weekly
  rollups into `traffic_daily`/`visitor_daily`/`daily_metrics`/
  `kpi_snapshots`, the PostgreSQL → Kafka → ClickHouse pipeline wiring
  (in-memory backbone/warehouse in dev/CI; Kafka/Zookeeper + ClickHouse in
  compose), read-only admin API with JWT RBAC + `X-Niche-Id`, and the
  analytics/revenue admin dashboards connected to real read models are
  implemented and tested. Follow-ups: production Kafka/ClickHouse
  provisioning and partitions, client/edge event SDK, retention/privacy
  jobs, sustained-load validation, and the `AIOS.Analytics.Insights` gate
  (external AI OS).
- **Goal:** The measurement pipeline: events → Kafka → ClickHouse → read models → dashboards.
- **Scope:** `analytics-service` (event schema, collector, Kafka producers/consumers, ClickHouse writes, nightly rollups, `daily_metrics`, `traffic_daily`, `visitor_daily`, `kpi_snapshots`, `revenue_summaries`); client/edge event SDK; `AIOS.Analytics.Insights` display card; privacy (pseudonymization, retention).
- **Deliverables:** events flow end-to-end (page views, pin clicks, affiliate clicks); warehouse live with partitions; nightly rollups; dashboard read models; insights card.
- **Dependencies:** Phases 2, 3, 4, 6, 7, 8 (event producers).
- **Estimated Complexity:** XL.
- **Risk Level:** High (data volume, correctness, privacy).
- **Success Criteria:** load test sustains millions of events/day; rollups reconcile with ledger totals; dashboards load < 2 s; no PII in warehouse.

| Module detail | |
|---|---|
| **Files** | `services/analytics-service/src/*`, collector, consumers, rollup jobs, `apps/admin` analytics pages, `libs/contracts/analytics/*` |
| **Folders** | `services/analytics-service/`, `libs/contracts/analytics/`, `infra/iac/clickhouse*`, `infra/iac/kafka*` |
| **Dependencies** | Phases 2, 3, 4, 6, 7, 8 |
| **Database tables used** | `analytics_events` (ClickHouse), `daily_metrics`, `traffic_daily`, `visitor_daily`, `kpi_snapshots`, `revenue_summaries` |
| **API contracts used** | Public Read (metrics for dashboards), `AIOS.Analytics.Insights`, events `affiliate:click`, `pin:*`, `content:*` |
| **Future integrations** | Mobile analytics, attribution refinements, alerting |
| **Testing requirements** | Event schema validation, load tests, rollup reconciliation tests, privacy/pseudonymization tests, warehouse retention tests |

### Phase 11 — Admin Dashboard

- **Status:** ✅ Complete (M9, v0.9.0 — ADR-0009). Admin & operations
  control plane: frozen RBAC catalog + system-role matrix seeded
  idempotently, operator identity management with niche-scoped role
  assignment, MFA-gated privileged actions and revocable sessions,
  append-only searchable audit ledger with capped CSV export,
  operations dashboard (sibling-service probes, queue visibility, job
  runs, failure counts), searchable webhook/operation logs with safe
  bounded retry, tenancy isolation verification, notifications, and
  HMAC-verified internal event ingestion are implemented and tested.
  Follow-ups: live TOTP verification and OIDC (Authentication milestone),
  PDF exports, and approval notification routing.
- **Goal:** The complete operations surface: all admin pages, RBAC views, notifications, exports.
- **Scope:** all admin pages per design system §11.2 (Dashboard, Analytics, Revenue, Pinterest, Automation, Settings); read-model consumption; RBAC-driven views; notification center; audit viewer; export tooling; admin service commands complete.
- **Deliverables:** full admin suite; role-based visibility; audit search; CSV/PDF exports; settings management.
- **Dependencies:** Phases 5 (auth), 6–10 (read models), 2 (frontend), 4.
- **Estimated Complexity:** XL.
- **Risk Level:** Medium.
- **Success Criteria:** every admin flow e2e-tested; role matrix enforced UI + API; audit searchable; exports validated.

| Module detail | |
|---|---|
| **Files** | `apps/admin/src/app/{dashboard,analytics,revenue,pinterest,automation,settings}/`, admin-service commands, `libs/contracts/admin/*` |
| **Folders** | `apps/admin/`, `services/admin-service/`, `libs/contracts/admin/` |
| **Dependencies** | Phases 2, 4, 5, 6, 7, 8, 9, 10 |
| **Database tables used** | Read models + `api_keys`, `admin_preferences`, `notifications*`, `audit_logs` |
| **API contracts used** | Admin API, read-model APIs, events for live updates |
| **Future integrations** | Compliance exports, delegation, approval notifications |
| **Testing requirements** | Admin e2e flows, RBAC tests, audit immutability tests, export tests, performance tests (dashboard < 2 s) |

### Phase 12 — Automation

- **Status:** 🟢 Complete — M10 foundation (v0.10.0, ADR-0010) and
  Step 2 business executors (v0.11.0, ADR-0011). The foundation provides
  durable rule/run state machines, Platform `scheduled_jobs` / `job_runs` /
  `queue_items` integration (tables remain admin-owned per ADR-0009,
  mapped by identical table names — no competing migrations), idempotent
  rule triggers, AI OS job correlation records (`aios_job_records`,
  `UNIQUE (job_id, contract)`, metadata only), exponential-backoff retry
  policy, and 10-niche isolation. Step 2 adds the production execution
  engine: executor abstraction + registry, five business executors
  (Pinterest publish, sitemap rebuild, affiliate reconciliation, analytics
  rollup, AI OS dispatch via the Bridge only), a real Celery worker with
  late-ack idempotent redelivery, a DB-driven single-scheduler Beat with
  Redis lock, best-effort job notifications to the admin internal channel,
  and a functional `/automation` admin UI. Remaining follow-ups are
  production-time validations: 30-day scheduler reliability and load.
- **Goal:** Business automation: scheduler, queues, notifications, and governance of automated work.
- **Scope:** `automation_rules`/`automation_runs`; `scheduled_jobs`/`job_runs`; `queue_items` ledger; Celery workers + Beat; notification delivery (in-app + email); pin-queue automation (with Phase 8); report generation; sitemap rebuild jobs; reconciliation jobs; automation dashboard controls; `aios_job_records` lifecycle.
- **Deliverables:** scheduled jobs execute reliably (pins, sitemaps, reports, reconciliation); automation rules manageable from the dashboard; notifications delivered; failures alert + retry.
- **Dependencies:** Phases 4, 5, 6, 7, 8, 9, 10, 11.
- **Estimated Complexity:** M.
- **Risk Level:** Medium.
- **Success Criteria:** no missed runs over 30 days; retry/backoff correct; alerts fire on failure; every automation action audited.

| Module detail | |
|---|---|
| **Files** | service workflow modules, `pipelines/jobs/*`, Celery configs, `apps/admin` automation pages, `libs/contracts/admin` (automation) |
| **Folders** | `services/*/workflows/`, `pipelines/jobs/`, `apps/admin/src/app/automation/` |
| **Dependencies** | Phases 4, 5, 6, 7, 8, 9, 10, 11 |
| **Database tables used** | `automation_rules`, `automation_runs`, `scheduled_jobs`, `job_runs`, `queue_items`, `notifications*`, `aios_job_records` |
| **API contracts used** | Admin API (automation), internal events, webhooks (status feeds) |
| **Future integrations** | Temporal (if workflows outgrow Celery), more channels |
| **Testing requirements** | Scheduler reliability tests, retry/backoff tests, failure-alert tests, audit tests, queue-ledger recovery tests |

### Phase 13 — Production Deployment

- **Status:** 🟡 In progress — M11 Phase 1 (production audit +
  infrastructure hardening, v0.12.0, ADR-0012) complete: non-root
  read-only images, resource limits, trust-zone network isolation, Caddy
  TLS edge, production compose profile (`infra/docker/compose.prod.yml`),
  fail-fast production secrets guard (backend-core), and CI enforcement
  (`tools/dev/check-infra.sh` + `docker compose config -q`). Phase A audit
  recorded in `docs/operations/001-production-audit.md`. Follow-ups:
  M11 Phase 2 (v0.13.0, ADR-0013) implemented Phases C–G: Vault client +
  store auth (Redis/ClickHouse/Kafka) + rotation policy, observability
  stack (Prometheus/Alertmanager/Grafana/OTel/Loki/Promtail) with SLO
  alerts and queue metrics, automated backup + CI-tested restore drill,
  deployment/rollback workflow scaffold, and failure-injection tests.
  Remaining: production rollout (Phase F runner + secrets), 30-day
  reliability validation, and final Go/No-Go (Phase H gates).
- **Goal:** Production go-live: environments, security, monitoring, DR, and launch.
- **Scope:** production IaC; Cloudflare CDN/WAF/DNS; Vercel + Fly.io deployments; Vault production; observability SLOs + alerting; backup/DR drills; load tests at target scale; security review; **Website Contract ratification**; runbooks in `docs/operations/`; go-live checklist.
- **Deliverables:** production environment live; monitoring dashboards + alerts; DR plan + successful drill; load test report; security review sign-off; go-live checklist signed.
- **Dependencies:** All phases 1–12.
- **Estimated Complexity:** L.
- **Risk Level:** High (launch risk).
- **Success Criteria:** SLOs met for 30 days; load tests pass at target scale (millions of articles/pins, 10 accounts); DR drill passes; security review closed; go-live checklist completed.

| Module detail | |
|---|---|
| **Files** | `infra/iac/environments/*`, `infra/observability/*`, `pipelines/ci/*`, `docs/operations/*`, `infra/secrets/*` |
| **Folders** | `infra/`, `pipelines/`, `docs/operations/`, `.github/workflows/` (deploy) |
| **Dependencies** | Phases 1–12 |
| **Database tables used** | Full production topology (all blueprint tables, partitioned + backed up) |
| **API contracts used** | All frozen contracts in production |
| **Future integrations** | Multi-region, edge functions, cost dashboards |
| **Testing requirements** | Load tests, chaos tests, DR drill, security pen-test, post-deploy smoke tests |

---

## 5. Milestone roadmap

### M1 — Foundation
**Phases:** 1.
**Goal:** The repository is a governed, buildable monorepo.
**Definition of Done:**
- [ ] All blueprint folders exist with README stubs.
- [ ] CI green (lint, format, contract validation, no-AI dependency scan, secret scan).
- [ ] `make setup` + `docker compose up` healthy on a clean machine.
- [ ] ADR process documented; CHANGELOG discipline active.

### M2 — Core Skeleton
**Phases:** 2, 3, 4.
**Goal:** Frontend, backend, and database foundations are real and connected.
**Definition of Done:**
- [ ] Web + admin apps render with the design system at all breakpoints; axe checks pass.
- [ ] Gateway and all services boot; `/health` green; OTel traces visible.
- [ ] All blueprint tables migrated; tenancy constraint tests pass.
- [ ] Contract packages build + validate; mock AI OS heartbeat works.
- [ ] Backup + restore drill passes in staging.

### M3 — Identity & First Content
**Phases:** 5, 6.
**Goal:** Operators can log in and publish content end-to-end.
**Definition of Done:**
- [ ] Admin login with MFA; RBAC enforced; audit trail verified.
- [ ] Publish flow e2e: create → review → approve → serve article page from DB.
- [ ] `AIOS.Content.Intake` works against the real AI OS (M3 gate); dedupe verified.
- [ ] Content events consumed by search/analytics stubs.
- [ ] Article page passes CWV budgets.

### M4 — Monetization
**Phases:** 7.
**Goal:** The site earns: catalog, links, attribution, and revenue.
**Definition of Done:**
- [ ] Product ingest from the first network; product + collection pages live with disclosure.
- [ ] `/go/{token}` redirect with attribution; click dedupe ≥ 99.9%.
- [ ] Commission webhooks processed; revenue summaries reconcile with network reports.
- [ ] Revenue events flow to analytics.

### M5 — Traffic Engine
**Phases:** 8.
**Goal:** Pinterest becomes a predictable traffic channel at 10-account scale.
**Definition of Done:**
- [x] 10 accounts configured per niche with zero cross-account leaks (tests).
- [ ] Boards sync; pins schedule and publish via Pinterest API; `AIOS.Pinterest.Assets` gate passed (AI OS gate pending — external dependency).
- [x] Rate-limit isolation verified (one account's throttle never blocks others).
- [x] Landing pages live; pin attribution events flow.

### M6 — Discovery
**Phases:** 9, 10.
**Goal:** The site is findable and measurable.
**Definition of Done:**
- [x] Sharded sitemaps + JSON-LD validated (v0.7.0).
- [ ] GSC/Bing data ingested; `AIOS.SEO.Metadata` gate passed (external AI OS + live credentials pending).
- [x] Event pipeline wired (PostgreSQL → Kafka → ClickHouse) and rollups reconcile with ledgers (v0.8.0).
- [ ] Event pipeline sustains target load (production load-test follow-up).
- [x] Analytics + revenue dashboards serve analytics read models (v0.8.0); SEO dashboards consume live sitemap/robots/search data (v0.7.0).
- [ ] Sub-2s dashboard performance budget validated in production (follow-up).
- [ ] `AIOS.Analytics.Insights` card renders read-only (external AI OS gate pending); no PII in warehouse (privacy guard + retention jobs follow-up).

### M7 — Operations
**Phases:** 11, 12.
**Goal:** Operators fully control the business through the admin suite and automation.
**Definition of Done:**
- [x] All admin pages live; role matrix enforced; audit searchable (v0.9.0).
- [x] Automation rule/run/queue state machines + idempotent triggers governable and
      audited with 10-niche isolation (v0.10.0 — M10 automation foundation).
- [x] Business executors wired (Pinterest publish, sitemap rebuild, affiliate
      reconciliation, analytics rollup, AI OS dispatch) with retry/backoff and
      notifications delivered to the admin channel (v0.11.0 — M10 Step 2).
- [ ] Scheduled jobs reliable for 30 days at production load (production follow-up).

### M8 — Production
**Phases:** 13.
**Goal:** Production go-live.
**Definition of Done:**
- [x] Infrastructure hardening: non-root read-only images, resource limits,
      network isolation, TLS edge, prod compose profile, secrets guard, CI
      enforcement (v0.12.0 — M11 Phase 1; audit in docs/operations/001).
- [x] Secrets + store auth (Vault boundary, Redis/ClickHouse/Kafka auth,
      rotation policy), observability + SLO alerts + queue metrics,
      automated backup with CI restore drill, deployment/rollback workflow
      scaffold, failure-injection tests (v0.13.0 — M11 Phase 2;
      docs/operations/002–006).
- [ ] Production environment live behind CDN/WAF; deploys green (Phases D–F).
- [ ] Production rollout executed; staging + prod deploys green (Phase F
      runner + secrets).
- [ ] SLOs met for 30 days; load tests pass at target scale (Phase H gate).
- [ ] DR drill passes in production; RPO/RTO actuals recorded (Phase H gate).
- [ ] Security review closed; final Go/No-Go signed (Phase H gate);
      Website Contract ratified.
- [ ] Go-live checklist signed; runbooks published.

---

## 6. Roadmap governance

- **Progress tracking:** milestone DoDs are the only definition of "done"; a phase closes only with its DoD (completed checkbox list) and a `CHANGELOG.md` entry.
- **Dependency enforcement:** a phase's start is blocked until all dependency DoDs pass; the order in Section 3 is binding.
- **AI OS boundary:** every phase keeps the no-AI-duplication rule; CI enforces it from M1.
- **Changes:** roadmap changes require an ADR, review by the Lead Software Architect and TPM, and a `CHANGELOG.md` entry. Scope added to a phase without DoD impact is rejected.
- **Task 9 begins** only after M1's Definition of Done passes; real code starts there.
