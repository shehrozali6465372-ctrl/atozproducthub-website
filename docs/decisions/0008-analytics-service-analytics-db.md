# ADR-0008 — Analytics Service Owns the Analytics & Reporting Business Layer

- **Status:** Accepted
- **Date:** 2026-08-11
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 01-folder-structure.md, 05-api-flow.md, 11-database-architecture.md, 12-api-contracts.md, 14-implementation-roadmap.md

## Context

M8 is the measurement milestone. It must deliver first-party event
collection, an append-only operational ledger, an event pipeline
(PostgreSQL → Kafka → ClickHouse), daily/weekly rollups, niche-scoped read
models, and the admin analytics dashboard — inside the Website Architecture
Contract, with strict niche tenancy, strict Pinterest-account isolation,
append-only ledger rules, zero AI functionality, and no analytics
intelligence of its own (insights belong to the AI OS via
`AIOS.Analytics.Insights`).

The Database Blueprint (§5.15–§5.16) defines `analytics_events` (ClickHouse),
`traffic_daily`, `visitor_daily`, `daily_metrics`, and `kpi_snapshots`, and
API Contracts define eventing and the collector, but service ownership,
tenancy transport, collector privacy rules, rollup semantics, and the
pipeline wiring are unspecified, so this ADR freezes those decisions.

## Decision

### 1. `services/analytics-service` owns the analytics database (`analytics_db`)

- The analytics module gets its own Alembic migration stream
  (`services/analytics-service/db/migrations/`), revision `0001`, with its
  own version table (`alembic_version_analytics`) so the content,
  affiliate, Pinterest, SEO, and analytics streams apply to the same
  physical database without interfering (same policy as ADR-0005/0006/0007).
- `analytics_db` holds only business data: local niche mirror, the
  append-only event ledger, and the daily read models. Raw analytics events
  also stream to the ClickHouse warehouse (`analytics_events`), which is
  infrastructure created outside this migration stream.
- CI validates the analytics migration stream against the same fresh
  PostgreSQL 16 used by the other services, including downgrade/re-upgrade.

### 2. Local tenancy mirror and strict account isolation

- Every `analytics_db` business record carries `niche_id` (Database
  Blueprint §4). Pinterest-scoped rows additionally carry
  `pinterest_account_id` so 10 accounts can coexist without mixing data.
- Cross-database foreign keys to `content_db.niches` are impossible, so
  `analytics_db` keeps its own minimal `analytics_niches` mirror
  (slug + name + status), read-only inside the service.
- Public collector routes identify the niche by slug (never by id); admin
  routes use the mandatory `X-Niche-Id` header and JWT RBAC
  (`analytics:read`/`analytics:write`). Every query and mutation is
  niche-scoped server-side; `account_id` additionally filters
  Pinterest-account data.

### 3. Append-only event ledger

- `analytics_event_ledger` is append-only: rows are never updated or
  deleted (enforced in the repository layer). `event_id` is unique, which
  makes ingestion idempotent: repeated deliveries return `duplicate` and
  never create a second row.
- Server-side timestamps are authoritative (`received_at`); client-supplied
  `occurred_at` is best-effort and validated.
- The collector applies a sensitive-trait guard: traits with keys such as
  `email`, `phone`, `password`, `ssn`, `credit_card`, `token`,
  `authorization`, or `api_key` are rejected before they reach the ledger.

### 4. Pipeline: PostgreSQL → Kafka → ClickHouse

- The service exposes an `EventBackbone` ABC and a `Warehouse` ABC.
  Production uses a Kafka producer (`KAFKA_ENABLED=true`) and a ClickHouse
  HTTP writer (`WAREHOUSE_ENABLED=true`); dev/CI use in-memory
  implementations so tests and smoke runs need no infrastructure.
- A `PipelineWorker` drains the backbone into the warehouse. The operational
  ledger in PostgreSQL is the durable source of truth; ClickHouse is the
  analytical store (Database Blueprint §5.16, §11).
- Domain events are consumed over the internal webhook endpoint
  (`/webhooks/v1/analytics/events`, HMAC-SHA256 with the shared
  `event_webhook_secret`): `content:published/updated/unpublished.v1`,
  `pin:published/failed.v1`, `product:ingested/removed.v1`,
  `affiliate:click.v1`, `revenue:attributed.v1`, and
  `seo:sitemap-rebuilt.v1`. Unknown domain event types are rejected, so
  producers cannot inject arbitrary analytics data.

### 5. Rollups and read models

- `run_rollups` aggregates the ledger into `traffic_daily`,
  `visitor_daily`, and `daily_metrics` with idempotent upserts (weekly
  snapshots land on Sundays). Read models are rebuilt from the ledger, never
  edited in place.
- Admin reads (overview, traffic, visitors, metrics, top pages, events,
  KPIs, pipeline status) are read-only analytical views with date-range
  filtering and optional `account_id` scoping.

### 6. AI OS boundary

- The analytics service contains zero AI: no model SDKs, no prompts, no
  embeddings, no vector storage, no LLM calls, no intelligence of its own.
  It stores and aggregates business events only.
- AI-derived insights are read-only attributed data that can only arrive
  through the existing `Website → AI OS Bridge → AI OS` path
  (`AIOS.Analytics.Insights` contract); the service never computes
  recommendations or predictions.

## Consequences

- The analytics module follows the M4–M7 service conventions exactly:
  domain entities, niche-scoped repositories, an `AnalyticsUnitOfWork`, an
  `AnalyticsService` facade, public/admin/webhook routes, RFC7807 errors,
  and a full test suite (collector idempotency, sensitive-data guard,
  webhook signature verification, rollup correctness, pipeline draining,
  cross-niche and cross-account isolation, migrations, and HTTP-level
  tenancy).
- The admin dashboard connects to the real analytics API through the typed
  `api.analytics.*` client namespace (`NEXT_PUBLIC_ANALYTICS_API_BASE_URL`),
  rendering KPI cards, traffic charts, source share, top pages, and
  affiliate/revenue metrics from the read models. It stays read-only — no
  chat, no generation.
- Kafka/ClickHouse provisioning (topics, databases, partitions) and real
  production credentials remain operator follow-ups; dev/CI default to the
  in-memory pipeline, and the compose stack includes Kafka (with
  Zookeeper) and ClickHouse so the production wiring can be validated.

## Contract compliance

- **No AI duplication:** the analytics service contains no intelligence;
  the no-AI CI guard scans it and `pip-audit` blocks AI SDKs.
- **Business layer only:** the service collects, validates, stores, and
  aggregates business events; insights belong to the AI OS and enter the
  website only through the AI OS Bridge.
- **Tenancy:** every `analytics_db` business record carries `niche_id`;
  Pinterest rows carry `pinterest_account_id`; cross-niche and cross-account
  leakage is impossible and covered by repository, service, and HTTP-level
  tests.
- **Privacy:** collector traits are schema-validated and filtered for
  sensitive keys before persistence.
