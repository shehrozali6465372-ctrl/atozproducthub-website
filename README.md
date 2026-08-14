# AtozProductHub Website

> The business layer of AtozProductHub: a content-driven website for articles, affiliate products, Pinterest, SEO, traffic, revenue, analytics, automation, and the admin dashboard.

This repository is **exclusively** for the AtozProductHub website — the business layer. It is intentionally separate from the **Universal AI Content Operating System** (AI OS), which already exists and is maintained in its own repository.

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [Project Goals](#2-project-goals)
3. [Project Scope](#3-project-scope)
4. [Repository Rules](#4-repository-rules)
5. [Architecture Philosophy](#5-architecture-philosophy)
6. [Relationship with Universal AI Content Operating System](#6-relationship-with-universal-ai-content-operating-system)
7. ["No Duplicate Features" Policy](#7-no-duplicate-features-policy)
8. [Development Rules](#8-development-rules)
9. [Future Roadmap](#9-future-roadmap)
10. [Architecture](#architecture)

---

## 1. Project Vision

AtozProductHub aims to become a trusted, high-traffic product discovery and content platform that turns educational articles and curated affiliate product recommendations into sustainable revenue — powered by automation but owned by clear business logic.

The website is the face of the business: where readers land, where products are recommended, where traffic is captured, and where revenue is earned. The AI OS works behind the scenes; this website is what users see and interact with.

## 2. Project Goals

- Publish high-quality, SEO-optimized articles that attract organic traffic.
- Showcase and monetize curated affiliate products with full disclosure.
- Grow and automate a Pinterest-driven traffic channel.
- Capture, measure, and improve traffic, engagement, and revenue with analytics.
- Automate repetitive operational tasks without reinventing AI capabilities.
- Provide a clear, data-informed admin dashboard for business oversight.
- Keep the business layer simple, fast, secure, and maintainable.

## 3. Project Scope

### In Scope (this repository)

- Website and user-facing pages.
- Article publishing and content presentation.
- Affiliate product listings, linking, and disclosure.
- Pinterest integration (pins, boards, and traffic attribution).
- SEO implementation (metadata, sitemaps, structured data, performance).
- Traffic management and acquisition tooling.
- Revenue tracking and affiliate reporting.
- Analytics instrumentation and reporting.
- Business automation workflows.
- Admin dashboard for content, products, and business operations.

### Out of Scope (owned by the AI OS or other systems)

- AI content generation, model orchestration, or content intelligence.
- Any AI OS functionality, module, or pipeline — copied or reimplemented.
- The AI OS repository itself — it is never merged, copied, or forked here.

## 4. Repository Rules

- This repository contains **only** the website business layer.
- No AI OS code, files, or functionality may be imported, copied, or duplicated.
- No implementation code may be added until an approved scope/design doc exists.
- Keep documentation and code changes reviewable and minimal.
- Secrets must never be committed; use environment variables or a secret manager.
- Every user-facing change must be tracked in `CHANGELOG.md` under `Unreleased`.
- The repository root must always contain: `README.md`, `LICENSE`, `.gitignore`, `CHANGELOG.md`, and `CONTRIBUTING.md`.

## 5. Architecture Philosophy

- **Separation of concerns:** the business layer and the AI OS remain independent codebases with clearly defined boundaries.
- **Content-first, SEO-native:** every page is built with SEO, performance, and crawlability in mind.
- **Data-driven:** content, product, and traffic decisions follow analytics, not guesswork.
- **Boring technology:** prefer simple, well-supported, mainstream tools over clever or novel stacks.
- **Automation with boundaries:** automate business workflows, never AI OS capabilities.
- **Privacy and security first:** minimal data collection, secure defaults, and full affiliate disclosure compliance.

## 6. Relationship with Universal AI Content Operating System

- The **AI OS** is the content intelligence and automation engine. It **already exists** in its own repository.
- This repository is the **website/business layer** and never reimplements AI OS functionality.
- The two systems interact **only through documented, versioned interfaces** (e.g., APIs) defined in future integration documentation.
- No code is shared between repositories, and no module is copied in either direction.
- Integration changes are coordinated, reviewed, and documented before they land.

## 7. "No Duplicate Features" Policy

- **The AI OS already exists. Do not build, copy, or adapt any part of it here.**
- Any feature request or pull request that duplicates an existing AI OS capability will be **rejected** during review.
- When a feature seems to overlap with the AI OS, stop and ask: *"Does the AI OS already do this?"* If the answer is yes, integrate through its interface instead of reimplementing.
- This policy applies to code, architecture, and documentation.

## 8. Development Rules

- **Docs before code:** no implementation until scope, architecture, and data model docs are approved.
- **Separate concerns:** website changes belong here; AI OS changes belong in the AI OS repository.
- **Small, reviewable changes:** prefer focused commits and pull requests.
- **Conventional commits:** use `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, and `test:` prefixes.
- **Testing:** automated tests are required once implementation begins.
- **No secrets:** env files, keys, and tokens must never be committed.
- **Quality gates:** linting, formatting, and tests must pass before merging.
- **License compliance:** only MIT-compatible dependencies may be introduced.

## 9. Future Roadmap

- **Phase 0 — Foundation (current):** repository, documentation, and governance in place.
- **Phase 1 — Website foundation:** tech stack decision, design system, deployment pipeline, analytics scaffold.
- **Phase 2 — Articles:** publishing workflow, article templates, and SEO fundamentals.
- **Phase 3 — Affiliate products:** product catalog, affiliate links, disclosures, and revenue tracking.
- **Phase 4 — Pinterest:** pin automation, board management, and traffic attribution.
- **Phase 5 — SEO and traffic:** sitemaps, structured data, performance budgets, and growth experiments.
- **Phase 6 — Analytics and revenue:** dashboards, reporting, and optimization loops.
- **Phase 7 — Automation:** business workflow automation (notifications, reporting, publishing pipelines).
- **Phase 8 — Admin dashboard:** operations dashboard for content, products, and metrics.
- **Ongoing — AI OS integration:** connect to the AI OS through documented APIs only.

---

## Architecture

The complete website architecture (business layer only) is maintained in [docs/architecture](docs/architecture/README.md). It covers system layers, module boundaries, data flow, API flow, responsibilities, security boundaries, and deployment strategy — with the Universal AI Content Operating System treated strictly as an external system accessed only through the AI OS Bridge. The binding boundary rule is the [Website Architecture Contract](docs/architecture/09-website-architecture-contract.md), which must be ratified before any implementation begins. The permanent project folder blueprint is [01-folder-structure.md](docs/architecture/01-folder-structure.md). The permanent, frozen technology stack is [10-technology-stack.md](docs/architecture/10-technology-stack.md). The permanent production database blueprint is [11-database-architecture.md](docs/architecture/11-database-architecture.md). The frozen API contracts are [12-api-contracts.md](docs/architecture/12-api-contracts.md) and the permanent UI/UX design system is [13-ui-ux-design-system.md](docs/architecture/13-ui-ux-design-system.md). The master implementation roadmap is [14-implementation-roadmap.md](docs/architecture/14-implementation-roadmap.md).

---

## Development

Prerequisites: Python 3.11+, Node.js 20+, Docker, Docker Compose.

Backend (M3 — shared core, API gateway, and eight service skeletons):

```bash
make setup        # create .venv; install backend-core, gateway, and services
make check        # lint, format check, typecheck, no-AI guard, contract check, tests
make docker-up    # build and start api, aios-bridge, content + affiliate services, postgres, redis (compose)
make health       # GET /health on the gateway
```

The shared backend foundation lives in `libs/backend-core` (ADR-0003) and is
consumed by the gateway (`apps/api`) and every service under `services/`.
The AI OS Bridge (`services/aios-bridge`) is the only AI OS contact point;
the frozen v1 message schemas live in `libs/contracts/aios/`.

CMS (M4 — `services/content-service`): the content module owns the content
database (`content_db`) with its own Alembic migration stream:

```bash
cd services/content-service
DATABASE_URL="postgresql+asyncpg://atoz:atoz@localhost:5432/atoz" \
  python -m alembic -c db/migrations/alembic.ini upgrade head
```

Run the content-service (public read API + admin CMS API) with the gateway
issuing JWT access tokens and the `X-Niche-Id` header carrying the tenancy
context (ADR-0004). In development the frontends use mock fixtures unless the
content API is configured:

- `NEXT_PUBLIC_CONTENT_API_BASE_URL` — public/admin API base (web + admin).
- `NEXT_PUBLIC_NICHE_SLUG` — niche slug for the public site (default `kitchen`).
- `NEXT_PUBLIC_NICHE_ID` / `NEXT_PUBLIC_ADMIN_TOKEN` — dev admin tenancy + JWT.

Affiliate (M5 — `services/affiliate-service`): the affiliate module owns the
affiliate database (`affiliate_db`) with its own Alembic migration stream
(ADR-0005). Migrations run from the service directory:

```bash
cd services/affiliate-service
DATABASE_URL="postgresql+asyncpg://atoz:atoz@localhost:5432/atoz"   python -m alembic -c db/migrations/alembic.ini upgrade head
```

The service serves the public product/collection reads, the admin affiliate
catalog, the server-controlled `/api/v1/public/go/{token}` redirector, and
the conversion webhook receiver (`POST /webhooks/v1/{network_code}/conversion`
with HMAC signature verification and idempotent ingestion). Webhook secrets,
the link-token signing key, and the JWT secret default to dev-only values and
must be provisioned via Vault in production. Frontends use mock fixtures
unless the affiliate API is configured:

- `NEXT_PUBLIC_AFFILIATE_API_BASE_URL` — public affiliate API base (web + admin).
- `NEXT_PUBLIC_NICHE_SLUG` — niche slug for the public site (default `kitchen`).

The affiliate business layer never performs AI work: product selection,
recommendations, and intelligence belong to the Universal AI Content
Operating System and enter the website only through the AI OS Bridge
(Website Architecture Contract, ADR-0005 §Contract compliance).

Pinterest (M6 — `services/pinterest-service`): the Pinterest module owns the
Pinterest database (`pinterest_db`) with its own Alembic migration stream
(ADR-0006). Migrations run from the service directory:

```bash
cd services/pinterest-service
DATABASE_URL="postgresql+asyncpg://atoz:atoz@localhost:5432/atoz" \
  python -m alembic -c db/migrations/alembic.ini upgrade head
```

The service manages 10+ independent Pinterest accounts per niche with strict
`pinterest_account_id` isolation: OAuth 2.0 authorization-code connect
(PKCE + per-account state/CSRF), Vault-bound token records (token VALUES
never touch the database), typed Pinterest API v5 client with per-account
`org_read`/`org_write` rate limits, board/section sync, queue-based pin
publishing with idempotency + retry and a complete publishing-attempt
ledger, and per-account analytics storage. Admin API (`/api/v1/admin/*` with
JWT RBAC `pinterest:read`/`pinterest:write` + mandatory `X-Niche-Id`) and a
read-only public API (`/api/v1/public/*` by niche slug) are included. OAuth
client credentials, the state secret, and the JWT secret default to dev-only
values and must be provisioned via Vault in production; live Pinterest
connect requires a real Pinterest app and authorized users (Trial access is
not enough for production behavior). Frontends use mock fixtures unless the
Pinterest API is configured:

- `NEXT_PUBLIC_PINTEREST_API_BASE_URL` — public Pinterest API base (web).

The Pinterest business layer never performs AI work: pin design, copy, and
targeting intelligence belong to the Universal AI Content Operating System
and enter the website only through the AI OS Bridge (ADR-0006
§Contract compliance).

SEO & Discovery (M7 — `services/seo-service`): the SEO module owns the SEO
database (`seo_db`) with its own Alembic migration stream (ADR-0007).
Migrations run from the service directory:

```bash
cd services/seo-service
DATABASE_URL="postgresql+asyncpg://atoz:atoz@localhost:5432/atoz" \
  python -m alembic -c db/migrations/alembic.ini upgrade head
```

The service provides applied SEO metadata and canonical URL policy
(duplicate-URL prevention), robots rules that never block Pinterestbot or
its image proxy, JSON-LD + Open Graph output, sharded sitemaps at million-
URL scale, Google/Bing crawl-report boundaries (server-side credentials
only), and strictly niche-scoped search indexing backed by Typesense
(lexical only; PostgreSQL remains the source of truth). Public reads are
niche-scoped by slug; the admin API uses JWT RBAC
`seo:read`/`seo:write` + mandatory `X-Niche-Id`; domain events drive
indexing/de-indexing (`content:published/updated/unpublished.v1`,
`product:ingested/removed.v1`). The JWT secret, the event webhook secret,
and the Typesense API key default to dev-only values and must be provisioned
via Vault in production. Frontends use mock fixtures unless the SEO API is
configured:

- `NEXT_PUBLIC_SEO_API_BASE_URL` — public SEO/search API base (web).
- `NEXT_PUBLIC_NICHE_SLUG` — niche slug for the public site (default `kitchen`).

The site proxies robots and sitemaps at `/robots.txt`, `/sitemap.xml`, and
`/sitemaps/{group}-{n}.xml` from the SEO service. The SEO business layer
never performs AI work: metadata intelligence belongs to the Universal AI
Content Operating System and enters the website only through the AI OS
Bridge (ADR-0007 §Contract compliance).

Analytics & Reporting (M8 — `services/analytics-service`): the analytics
module owns the analytics database (`analytics_db`) with its own Alembic
migration stream (ADR-0008). Migrations run from the service directory:

```bash
cd services/analytics-service
DATABASE_URL="postgresql+asyncpg://atoz:atoz@localhost:5432/atoz"   python -m alembic -c db/migrations/alembic.ini upgrade head
```

The service runs a first-party event collector (`/collect/v1/events` and
`/collect/v1/events/batch`, slug-based niche tenancy, `event_id`
idempotency, append-only ledger, sensitive-trait guard), a HMAC-verified
domain-event webhook (`/webhooks/v1/analytics/events`), daily/weekly
rollups into `traffic_daily`, `visitor_daily`, `daily_metrics`, and
`kpi_snapshots`, and a read-only admin API (`/api/v1/admin/*` with JWT RBAC
`analytics:read`/`analytics:write` + mandatory `X-Niche-Id`). The event
pipeline is PostgreSQL → Kafka → ClickHouse; dev/CI use in-memory backbone
+ warehouse, and the compose stack includes single-node KRaft Kafka and ClickHouse
so production wiring can be validated. The event webhook secret and the JWT
secret default to dev-only values and must be provisioned via Vault in
production. The admin dashboard uses mock fixtures unless the analytics API
is configured:

- `NEXT_PUBLIC_ANALYTICS_API_BASE_URL` — admin analytics API base
  (apps/admin).

The analytics business layer never performs AI work: it stores and
aggregates business events only; AI-derived insights are read-only
attributed data that can arrive only through the AI OS Bridge (ADR-0008
§Contract compliance).


Admin & Operations (M9 — `services/admin-service`): the admin module owns
the admin database (`admin_db`) with its own Alembic stream
(`alembic_version_admin`), the frozen RBAC catalog + system-role matrix,
operator identity management with niche-scoped role assignment, the
append-only audit ledger with capped CSV export, the operations dashboard
(sibling-service probes, queue visibility, job runs, failure counts),
searchable webhook/operation logs with safe bounded retry, tenancy
isolation verification, notifications, and HMAC-verified internal event
ingestion. Privileged actions are MFA-gated and revocable sessions are
enforced (in-memory dev/CI, Redis production). The admin frontend pages
`/ops`, `/ops/logs`, and `/audit` render real admin API data when
`NEXT_PUBLIC_ADMIN_API_BASE_URL` is configured and fall back to mocks
otherwise. ADR-0009 freezes the service ownership and boundaries; the
control plane records and reports business operations only — no AI
functionality (Website Contract §4).

Automation (M10 — `services/automation-service`): the automation module owns
the automation database (`automation_db`) with its own Alembic stream
(`alembic_version_automation`): `automation_niches` (local mirror),
`automation_rules`, `automation_runs` (append-only history, idempotent
triggers), and `aios_job_records` (Bridge correlation metadata only —
`UNIQUE (job_id, contract)` dedupe). The Platform tables `scheduled_jobs`,
`job_runs`, and `queue_items` remain admin-owned (ADR-0009) and are
integrated by identical table mapping (ADR-0010). The foundation ships
rule/run state machines, the durable queue ledger with exponential-backoff
retries, and the job execution lifecycle. Step 2 (v0.11.0, ADR-0011) adds
the production execution engine: five business executors (Pinterest pin
publishing, sitemap rebuild, affiliate reconciliation, analytics rollup,
AI OS job dispatch) that orchestrate owning sibling services via
short-lived service-to-service JWTs, a real Celery worker + single-scheduler
Beat (Redis lock, croniter UTC), durable-ledger retries with late-ack
idempotent redelivery, and best-effort job notifications routed to the
admin internal channel. The admin `/automation` UI operates rules,
scheduled jobs, execution history, the queue ledger, and the executor
catalog against a JWT RBAC API under `/api/v1/admin` with strict
`X-Niche-Id` tenancy. The website remains a business platform; all
intelligence stays in the AI OS (Website Contract §4).

Frontend (M2 — web + admin wireframes on the shared design system):

```bash
npm ci            # install workspace dependencies (lockfile committed)
npm run dev:web   # public website  -> http://localhost:3000
npm run dev:admin # admin dashboard -> http://localhost:3001
npm run lint      # eslint (all workspaces)
npm run typecheck # tsc --noEmit (all workspaces)
npm test          # vitest + axe a11y tests (all workspaces)
npm run build     # next build (web + admin)
```

The implementation roadmap is [14-implementation-roadmap.md](docs/architecture/14-implementation-roadmap.md); M1 (foundation), M2 (frontend foundation), M3 (backend foundation), M4 (CMS business layer), M5 (affiliate engine), M6 (Pinterest business layer), M7 (SEO & discovery layer), M8 (analytics business layer), M9 (admin & operations layer), M10 (automation foundation + business executors) are complete; production (M11) follows.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening issues or pull requests.
