# 01 — Folder Structure (Permanent Project Folder Blueprint)

**Status:** Permanent blueprint — binding for all future implementation
**Version:** 2.0 (supersedes the earlier draft layout)
**Compliance:** Must always satisfy the [Website Architecture Contract](09-website-architecture-contract.md)

This document is the **single source of truth** for the project folder structure. It defines every folder, what it is for, what will live inside it, who owns it, and the conventions every contributor must follow.

---

## 1. Guiding rules

1. **Apps are thin.** Frontends (`apps/web`, `apps/admin`) and the API gateway contain presentation and routing only — no business logic.
2. **Services own their data.** Every backend service owns its domain and its schema (`db/migrations` lives inside the service). No shared tables, no cross-service database access.
3. **Contracts are the only shared code.** `libs/contracts` and `libs/domain-core` are the only code imported across module boundaries.
4. **One AI OS door.** Only `services/aios-bridge/` (and its contracts in `libs/contracts/aios/`) may contact the AI OS. Nothing else references it.
5. **No intelligence folders.** No folder, file, or dependency for AI generation, learning, research, memory, prompts, model routing, or LLM calls may ever exist here (Contract §4.2).
6. **Docs first.** The repository remains documentation-only until the contract is ratified and scope/design documents are approved.

---

## 2. Category map

How the fifteen required areas map to folders:

| Area | Primary location | Supporting location |
|------|------------------|---------------------|
| Frontend | `apps/web/`, `apps/admin/` | `apps/mobile/` (future) |
| Backend | `apps/api/` (gateway), `services/*/` | — |
| Database | `infra/db/` + `services/*/db/migrations/` | `config/` (connection config, non-secret) |
| APIs | `apps/api/`, `libs/contracts/` | `services/*/src/api/` (internal contracts) |
| Documentation | `docs/` | root `README.md`, `CHANGELOG.md` |
| Configuration | `config/` | `.env.example`, `infra/secrets/` (references only) |
| Infrastructure | `infra/` | `pipelines/` |
| Assets | `assets/` | `apps/*/public/` (app-specific) |
| SEO | `services/seo-service/` | `libs/contracts/seo/`, `apps/web` (rendering) |
| Affiliate | `services/affiliate-service/` | `libs/contracts/affiliate/` |
| Pinterest | `services/pinterest-service/` | `libs/contracts/pinterest/` |
| Analytics | `services/analytics-service/` | `libs/contracts/analytics/` |
| Admin | `apps/admin/`, `services/admin-service/` | `libs/contracts/admin/` |
| Automation | `pipelines/jobs/`, `services/*/workflows/` | `.github/workflows/` (CI/CD) |
| Testing | `tests/`, per-app `tests/`, per-service `tests/` | `tools/dev/` |

---

## 3. Complete directory tree

```
atozproducthub-website/
│
├── README.md                         # Project overview & index of documents
├── LICENSE                           # MIT license
├── CHANGELOG.md                      # Keep-a-Changelog release history
├── CONTRIBUTING.md                   # Contribution guide & boundaries
├── .gitignore                        # Ignore rules (deps, builds, secrets, OS files)
├── .editorconfig                     # Cross-editor formatting defaults          [future]
├── .env.example                      # Public template of environment variables  [future]
├── Makefile                          # Common developer commands                 [future]
├── package.json                      # Root Node.js workspace (dev tooling only) [future]
├── pyproject.toml                    # Root Python tooling (dev tooling only)    [future]
│
├── docs/                             # DOCUMENTATION
│   ├── architecture/                 # Architecture set + Website Contract (populated today)
│   ├── decisions/                    # Architecture Decision Records (ADRs)      [future]
│   ├── operations/                   # Runbooks, incident and ops guides         [future]
│   └── guides/                       # Developer guides, onboarding              [future]
│
├── apps/                             # FRONTENDS + API ENTRYPOINT (thin)
│   ├── web/                          # Public website — React / Next.js
│   │   ├── src/
│   │   │   ├── app/                  # Next.js App Router routes (pages, layouts)
│   │   │   ├── components/           # UI components (PascalCase files)
│   │   │   ├── lib/                  # Client utilities + typed API client
│   │   │   └── styles/               # Global styles and design tokens
│   │   ├── public/                   # App-specific static assets (images, favicon)
│   │   ├── tests/                    # Component and page tests
│   │   ├── next.config.*             # Next.js configuration
│   │   ├── package.json              # App dependencies (self-contained)
│   │   └── README.md                 # App-local documentation
│   ├── admin/                        # Admin dashboard — React / Next.js
│   │   └── (same structure as apps/web)
│   ├── api/                          # Business API gateway — FastAPI
│   │   ├── src/
│   │   │   ├── routes/               # Public API, admin API, webhook receivers
│   │   │   ├── middleware/           # AuthN/Z, rate limiting, validation
│   │   │   └── clients/              # Typed clients to domain services
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   └── README.md
│   └── mobile/                       # FUTURE mobile app (documented, not created)
│
├── services/                         # BACKEND DOMAIN SERVICES — FastAPI (one per module)
│   ├── content-service/              # Articles, publishing, content lifecycle
│   │   ├── src/
│   │   │   ├── domain/               # Entities and business rules
│   │   │   ├── application/          # Use cases and workflows
│   │   │   ├── adapters/             # Storage, renderer, bridge adapters
│   │   │   └── api/                  # Internal API (consumed by gateway only)
│   │   ├── db/migrations/            # Schema migrations (owned by this service)
│   │   ├── workflows/                # Business automations (e.g., publish pipeline)
│   │   ├── tests/                    # Unit and integration tests
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   └── README.md
│   ├── pinterest-service/            # Accounts (10+), boards, pins, scheduling
│   ├── affiliate-service/            # Catalog, link tokens, clicks, commissions
│   ├── seo-service/                  # Metadata, sitemaps, structured data, health
│   ├── analytics-service/            # Events, metrics, reports, read models
│   ├── admin-service/                # Governance commands, audit log, settings
│   └── aios-bridge/                  # AI OS Bridge — THE ONLY AI OS CONTACT POINT
│       ├── src/
│       │   ├── adapters/             # AI OS API adapters (signature verify, mapping)
│       │   ├── jobs/                 # Job correlation, retries, circuit breaking
│       │   └── api/                  # Internal intake/status endpoints
│       ├── tests/
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── README.md                 # Documents the bridge boundary explicitly
│
├── libs/                             # SHARED CODE — CONTRACTS ONLY
│   ├── contracts/                    # OpenAPI (sync) + AsyncAPI (events) schemas
│   │   ├── content/
│   │   ├── pinterest/
│   │   ├── affiliate/
│   │   ├── seo/
│   │   ├── analytics/
│   │   ├── admin/
│   │   └── aios/                     # AI OS integration contracts (v1 intake/status/etc.)
│   └── domain-core/                  # Pure value types, identifiers, enums (no behavior)
│
├── config/                           # CONFIGURATION — NON-SECRET, PER ENVIRONMENT
│   ├── dev/                          # Local development settings
│   ├── staging/                      # Staging settings
│   └── prod/                         # Production settings
│       ├── env.template              # Variable templates (values never committed)
│       └── secrets.refs              # References to vault entries (never values)
│
├── infra/                            # INFRASTRUCTURE
│   ├── iac/                          # Terraform/Pulumi: networking, compute, stores
│   │   ├── environments/             # dev / staging / prod
│   │   └── modules/                  # Reusable infrastructure modules
│   ├── docker/                       # Compose files, base images, image policies
│   ├── db/                           # DB infrastructure: init, backup, partitioning
│   ├── observability/                # Dashboards, alert rules, SLOs as code
│   └── secrets/                      # Vault policies and references — NEVER secrets
│
├── assets/                           # ASSETS — SHARED BRAND & MEDIA
│   ├── brand/                        # Logos, favicons, fonts, color tokens
│   ├── images/                       # Shared/default imagery (social cards etc.)
│   └── templates/                    # Non-code templates (disclosure banners, layouts)
│
├── pipelines/                        # AUTOMATION & CI/CD
│   ├── ci/                           # Reusable CI/CD pipeline templates
│   └── jobs/                         # Scheduled business automations (reports, sitemaps)
│
├── tests/                            # CROSS-CUTTING TESTING
│   ├── e2e/                          # End-to-end business flows
│   ├── load/                         # Load and scale tests (articles, pins, clicks)
│   └── smoke/                        # Post-deploy smoke checks
│
├── tools/                            # DEV TOOLING
│   ├── dev/                          # Local orchestration scripts (up, lint, test)
│   └── codegen/                      # Contract → client generation            [future]
│
└── .github/                          # CI/CD — GitHub Actions
    └── workflows/                    # CI, CD, scheduled jobs, dependency scans
```

Legend: entries marked `[future]` are planned; everything else is part of the permanent blueprint. Today only `docs/` is populated.

---

## 4. Folder dictionary

Owner roles: `@atoz/lead` = Lead Software Architect, `@atoz/platform` = platform/infra, `@atoz/web` = website frontend, `@atoz/admin` = admin frontend, `@atoz/content` = content module, `@atoz/pinterest` = Pinterest module, `@atoz/affiliate` = affiliate module, `@atoz/seo` = SEO module, `@atoz/analytics` = analytics module, `@atoz/governance` = admin/governance module, `@atoz/bridge` = AI OS Bridge module.

### Root level

**`README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `.gitignore`**
- **Purpose:** Required repository foundation (Contract/Repository Rules — these five files must always exist).
- **Responsibility:** Identity, licensing, release history, contribution rules, ignore policies.
- **Owner:** `@atoz/lead`
- **Future modules:** none — root files stay minimal.

**`.editorconfig`, `.env.example`, `Makefile`, `package.json`, `pyproject.toml`**
- **Purpose:** Root-level developer conveniences and tooling.
- **Responsibility:** Consistent formatting, public env variable template, common commands, root dependency manifests for dev tooling only.
- **Owner:** `@atoz/platform`
- **Future modules:** shared lint/format/contract-validation commands.

### `docs/`
- **Purpose:** All project documentation lives here.
- **Responsibility:** Architecture, decisions, operations, and developer guidance; every proposal starts as a doc.
- **Owner:** `@atoz/lead` (architecture & decisions); module owners for their guides.
- **Future modules:** API usage guides, admin operator manuals, onboarding docs.

### `apps/`
- **Purpose:** Thin deployables: the public website, the admin dashboard, the API gateway, and the future mobile app.
- **Responsibility:** Rendering, routing, request entry, client behavior. No business logic.
- **Owner:** `@atoz/web` (`web`), `@atoz/admin` (`admin`), `@atoz/platform` (`api`, `mobile` future).
- **Future modules:** `apps/mobile` (React Native), additional marketing/landing surfaces.

**`apps/web/`** — Public website (React / Next.js).
- **Purpose:** Reader-facing surface: articles, product pages, hubs, pin landing pages, SEO tags.
- **Responsibility:** Page rendering, SEO tag output, client analytics SDK, consent UI, affiliate disclosure UI.
- **Owner:** `@atoz/web`
- **Future modules:** multilingual views, related-content widgets, mobile web optimization.

**`apps/admin/`** — Admin dashboard (React / Next.js).
- **Purpose:** Operator surface for content, Pinterest, affiliate, SEO, analytics, settings.
- **Responsibility:** Dashboard rendering, read-model consumption, management commands via the gateway.
- **Owner:** `@atoz/admin`
- **Future modules:** approval notification panels, role delegation UI.

**`apps/api/`** — Business API gateway (FastAPI).
- **Purpose:** Single entry point for public reads, admin writes, and webhooks.
- **Responsibility:** Routing, authN/Z, rate limiting, validation, idempotency, webhook signature verification (pass-through to services).
- **Owner:** `@atoz/platform`
- **Future modules:** mobile app API keys, partner/exporter endpoints.

### `services/`
- **Purpose:** Backend domain services — one per bounded context (see `03-module-boundaries.md`). FastAPI.
- **Responsibility:** Enforce business rules, own their data and workflows, emit versioned events.
- **Owner:** the owning module role listed per folder.
- **Future modules:** revenue-reconciliation service, multilingual service, referral/community service — always as new `services/*/` folders, never as new AI folders.

**`services/content-service/`** — Articles, publishing, content lifecycle.
- **Responsibility:** Intake validation, dedupe, immutable storage, publish events, renderer triggers.
- **Owner:** `@atoz/content`
- **Future modules:** newsletter digests, related-content read APIs.

**`services/pinterest-service/`** — Pinterest accounts (10+), boards, pins, scheduling.
- **Responsibility:** Per-account registry and rate-limit budgets, pin queue, append-only pin ledger, attribution metadata.
- **Owner:** `@atoz/pinterest`
- **Future modules:** additional visual channels.

**`services/affiliate-service/`** — Catalog, link tokens, clicks, commissions.
- **Responsibility:** Product feed ingestion, signed link tokens, click attribution, commission ledger, disclosures.
- **Owner:** `@atoz/affiliate`
- **Future modules:** new networks, payout reporting, reviews/ratings.

**`services/seo-service/`** — Metadata, sitemaps, structured data, SEO health.
- **Responsibility:** Apply approved SEO metadata, generate sharded sitemaps and JSON-LD, enforce URL policy, health reporting.
- **Owner:** `@atoz/seo`
- **Future modules:** multilingual hreflang, site search hooks.

**`services/analytics-service/`** — Events, metrics, reports.
- **Responsibility:** Event schema, collection, warehouse partitions, metric definitions, report read models.
- **Owner:** `@atoz/analytics`
- **Future modules:** mobile app analytics, channel attribution refinements.

**`services/admin-service/`** — Governance commands, audit log, settings.
- **Responsibility:** Moderation/approval workflows, audit trail, business settings, automation scheduling (business workflows only).
- **Owner:** `@atoz/governance`
- **Future modules:** compliance exports, role delegation.

**`services/aios-bridge/`** — AI OS Bridge (the only AI OS contact point).
- **Responsibility:** AI OS adapters, schema mapping, signature verification, job correlation, retries, circuit breaking.
- **Owner:** `@atoz/bridge`
- **Future modules:** new AI OS contracts as they are added upstream — always through this folder.
- **Boundary note:** contains adapter code only. No prompts, models, generation, learning, or memory — ever.

### `libs/`
- **Purpose:** The only shared code in the repository.
- **Responsibility:** Versioned API/event contracts and pure shared types.
- **Owner:** `@atoz/lead`
- **Future modules:** any new contract namespace follows the same pattern.

**`libs/contracts/`** — OpenAPI/AsyncAPI schemas, one namespace per module.
- **Responsibility:** Versioned, reviewed contracts; the only way modules exchange data.
- **Future modules:** `/v2/` versions when breaking changes are approved.

**`libs/domain-core/`** — Pure identifiers, value types, enums.
- **Responsibility:** Shared vocabulary used by contracts. No behavior, no imports of services/apps.
- **Future modules:** shared niche/account scoping types.

### `config/`
- **Purpose:** Non-secret, environment-scoped configuration.
- **Responsibility:** Env templates, app settings, references to vault entries. Values never committed.
- **Owner:** `@atoz/platform`
- **Future modules:** feature-flag definitions, per-niche configuration templates.

### `infra/`
- **Purpose:** Everything that runs and connects the platform.
- **Responsibility:** IaC, Docker, database infrastructure, observability, secrets policy.
- **Owner:** `@atoz/platform`
- **Future modules:** multi-region, cost dashboards, compliance tooling.

**`infra/iac/`** — Terraform/Pulumi.
- **Responsibility:** Networking, compute, stores, CDN; per-environment stacks.
- **Future modules:** edge compute, failover stacks.

**`infra/docker/`** — Compose, base images, image policies.
- **Responsibility:** Local dev environment (apps + services + PostgreSQL + Redis), production image conventions.
- **Future modules:** additional runtimes only with ADR approval.

**`infra/db/`** — Database infrastructure.
- **Responsibility:** Cluster/instance setup, init scripts, backups, partitioning and retention policies. (Schemas themselves live per-service.)
- **Future modules:** read replicas, archival tooling.

**`infra/observability/`** — Dashboards, alerts, SLOs as code.
- **Responsibility:** Metrics, logs, traces configuration; alert rules.
- **Future modules:** cost observability, compliance reporting.

**`infra/secrets/`** — Vault policies and references.
- **Responsibility:** Define what is secret and who can read it. Never contains values.
- **Future modules:** automated rotation policies.

### `assets/`
- **Purpose:** Shared brand and media assets used by multiple apps.
- **Responsibility:** Logos, favicons, fonts, default images, non-code templates.
- **Owner:** `@atoz/web`
- **Future modules:** localized asset variants. Runtime-generated media (AI OS outputs such as article images and pin assets) is stored in object storage, never in this folder.

### `pipelines/`
- **Purpose:** Automation: reusable CI/CD templates and scheduled business jobs.
- **Responsibility:** Pipeline quality gates; scheduled automations (sitemap rebuilds, reports, pin queue maintenance).
- **Owner:** `@atoz/platform`
- **Future modules:** workflow orchestration for new automations — business workflows only, never AI OS automation.

### `tests/`
- **Purpose:** Cross-cutting test suites beyond unit tests.
- **Responsibility:** E2E business flows, load/scale validation (millions of articles/pins scenarios), post-deploy smoke checks.
- **Owner:** `@atoz/platform` (shared suites); module owners provide per-service tests.
- **Future modules:** contract-test suites, mobile e2e.

### `tools/`
- **Purpose:** Developer tooling, not product code.
- **Responsibility:** Local orchestration (`tools/dev/`) and future contract codegen (`tools/codegen/`).
- **Owner:** `@atoz/platform`
- **Future modules:** migration tooling, analytics query helpers.

### `.github/`
- **Purpose:** GitHub-native automation (CI/CD).
- **Responsibility:** Workflows: CI (lint/test/scan), CD (deploy), scheduled jobs, dependency and secret scanning.
- **Owner:** `@atoz/platform`
- **Future modules:** dependency-update automation, release automation.

---

## 5. Technology placement

| Technology | Where it lives | Notes |
|------------|----------------|-------|
| React / Next.js | `apps/web/`, `apps/admin/` | Each app is self-contained (own `package.json`); App Router; server components render; no business logic |
| FastAPI | `apps/api/` (gateway) and every `services/*/` | Each service is an independent FastAPI application |
| PostgreSQL | `infra/db/` (infrastructure) + `services/*/db/migrations/` (schemas) | Per-service schema ownership per the contract |
| Redis | `infra/docker/` (compose) + `config/` (connection config) | Cache and per-account pin/click queues |
| Docker | `infra/docker/` (compose, base images) + one `Dockerfile` per deployable | Local dev compose includes apps, services, PostgreSQL, Redis |
| CI/CD | `.github/workflows/` + `pipelines/ci/` | GitHub Actions; reusable templates in `pipelines/ci/` |
| AI OS Bridge | `services/aios-bridge/` + `libs/contracts/aios/` | Sole AI OS contact point; adapter + contracts only |

---

## 6. Repository conventions

### 6.1 Folder naming
- All folders: `kebab-case`, lowercase, hyphens (e.g., `content-service`, `db/migrations`).
- No folder contains implementation until its scope/design document is approved.
- Forbidden folder names anywhere in the tree: `ai/`, `ml/`, `models/`, `prompts/`, `training/`, `inference/`, `llm/`, `router/`, `memory/`, `research/`, `generation/`, `datasets/`, `weights/`, `agent/`.

### 6.2 File naming
- Documentation: `NN-name.md` in `docs/architecture/` (zero-padded numbers); ADRs `NNNN-title.md` in `docs/decisions/`.
- Python: `snake_case.py`; package names `atoz_<service>` (e.g., `atoz_content_service`).
- TypeScript/React: components `PascalCase.tsx`; other TS files `kebab-case.ts`; hooks `useCamelCase.ts`.
- Database: tables plural `snake_case` (`articles`, `pin_ledger`, `affiliate_clicks`); migrations `NNNN_description.sql`; indexes `idx_<table>_<columns>`.
- Environment variables: `UPPER_SNAKE_CASE` with scope prefixes (`APP_`, `DB_`, `REDIS_`, `PINTEREST_`, `AIOS_`).
- Branches: `docs/`, `feat/`, `fix/`, `chore/`, `refactor/`, `test/` (per `CONTRIBUTING.md`).
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).

### 6.3 Import rules
- Apps import service capabilities **only** through `libs/contracts/` (typed API clients) — never service internals.
- Services import only: their own package, `libs/contracts/`, `libs/domain-core/`, and standard libraries.
- **No cross-service imports.** If two services need something, it moves to `libs/contracts/` or `libs/domain-core/`.
- **No service reads another service's database.**
- `services/aios-bridge/` is the only place that imports AI OS client code. Other services consume AI OS outputs only through bridge contracts.
- Absolute imports from the package root; relative imports limited to one level. Enforced by linters/import-linter.

### 6.4 Dependency rules
- Dependencies are declared per app/service (`package.json` / `pyproject.toml`); the root manifests contain dev tooling only.
- Dependency graph is strictly one-way: `apps/ → services/ (via contracts) → libs/; libs/domain-core → nothing`.
- Lockfiles are committed; dependency versions are pinned.
- All dependencies must be MIT-compatible (root `README.md`, Development Rules).
- **No AI/ML/LLM/inference dependencies are permitted in any manifest.** CI dependency scanning enforces this.
- Adding a new shared library or shared folder requires an ADR (decision record) plus contract compliance review.

---

## 7. Verification against the Website Architecture Contract

| Contract requirement (09) | How this blueprint satisfies it |
|----------------------------|----------------------------------|
| §1 Locked statement | Tree contains business-layer folders only; zero intelligence folders or files |
| §4.1 Business-layer areas | Every business area (CMS, business, SEO, Pinterest, storefront, analytics, revenue, admin) maps to an `apps/` or `services/` folder |
| §4.2 Never contains AI machinery | No `ai/`, `ml/`, `models/`, `prompts/`, `training/`, `llm/`, `router/`, `memory/` folders; forbidden names listed in §6.1; CI blocks AI dependencies |
| §4.3 AI OS owns intelligence | No folder claims AI OS work; the AI OS remains a separate repository |
| §5 Only door — AI OS Bridge | `services/aios-bridge/` is the sole AI OS contact point; `libs/contracts/aios/` holds the versioned contracts |
| §6 Every feature passes the checklist | Folder/PR checklist: display/publish/measure/operate → business layer; generate/learn/research → AI OS (rejected here) |
| §7 Amendment process | Blueprint changes require an ADR + contract compliance review (see §9) |

## 8. Verification that NO AI Content OS functionality is duplicated

1. **Folder scan:** the tree defines no location for generation, learning, research, memory, prompts, routing, or inference — the forbidden-name list (§6.1) is enforced in review and CI.
2. **Dependency scan:** no manifest may declare AI/LLM/model dependencies; CI rejects them automatically.
3. **Bridge isolation:** `services/aios-bridge/` contains adapters, verification, and mapping only. It consumes AI OS output; it never reimplements it.
4. **Artifact flow:** approved AI OS outputs (articles, pin assets, SEO metadata) enter through bridge contracts and are stored in runtime object storage — never generated, edited, or committed in this repository.
5. **Single direction:** the website requests work and displays results; all intelligence stays in the AI OS repository.

## 9. Change process for this blueprint

- This document is the **permanent project folder blueprint**. It changes only by explicit amendment.
- Any change requires: an ADR in `docs/decisions/`, a contract-compliance review, `CHANGELOG.md` entry, and approval by `@atoz/lead`.
- A proposed change that would add AI functionality or duplicate AI OS features is rejected outright under the Website Architecture Contract §1 and §7.
