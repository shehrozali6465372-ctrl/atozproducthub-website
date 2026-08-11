# analytics-service

First-party analytics collection, append-only event ledger, daily/weekly
rollups, and niche-scoped report read models — M8 Analytics business layer
(ADR-0008).

- **Owner:** @atoz/analytics
- **Status:** M8 complete (v0.8.0) — business layer only, zero AI.
- **Database:** owns `analytics_db` tables (own Alembic stream, version
  table `alembic_version_analytics`) — `analytics_niches`,
  `analytics_event_ledger` (append-only, unique `event_id`),
  `traffic_daily`, `visitor_daily`, `daily_metrics`, `kpi_snapshots`.
  Raw events also stream to the ClickHouse warehouse (`analytics_events`),
  created outside this migration stream (Database Blueprint §5.16).
- **Pipeline:** PostgreSQL operational ledger → Kafka event backbone →
  ClickHouse analytical warehouse. Dev/CI default to in-memory backbone +
  warehouse; `KAFKA_ENABLED=true` / `WAREHOUSE_ENABLED=true` enable the real
  transports (compose includes single-node KRaft Kafka and ClickHouse).
- **Endpoints:**
  - Public collector: `/collect/v1/events` and `/collect/v1/events/batch`
    — slug-based niche tenancy, `event_id` idempotency, sensitive-trait
    guard, server-side timestamps, append-only.
  - Admin: `/api/v1/admin/*` — JWT RBAC `analytics:read`/`analytics:write`
    + mandatory `X-Niche-Id` header; read-only overview, traffic, visitors,
    metrics, top pages, events, KPIs, pipeline status, and rollup runs.
  - Webhooks: `/webhooks/v1/analytics/events` — HMAC `X-Event-Signature`
    verified domain-event ingestion (`content:*`, `pin:*`, `product:*`,
    `affiliate:click`, `revenue:attributed`, `seo:sitemap-rebuilt`).
  - Shared: `/health`, `/ready`, `/metrics` (backend-core factory).
- **Migrations:** `db/migrations/` — `DATABASE_URL`-driven; validated
  against fresh PostgreSQL 16 in CI (upgrade, schema check, downgrade +
  re-upgrade).
- **Admin dashboard:** `apps/admin` connects through the typed
  `api.analytics.*` client namespace when
  `NEXT_PUBLIC_ANALYTICS_API_BASE_URL` is set; without it the admin app
  renders mock fixtures so it works standalone.
- **AI OS boundary:** this service never contacts the AI OS directly and
  contains zero AI logic. It stores and aggregates business events only;
  AI-derived insights are read-only attributed data that can arrive only
  through `services/aios-bridge/` + `libs/contracts/aios/`.
