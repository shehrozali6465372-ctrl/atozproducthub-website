# ADR-0009 — Admin Service Owns the Admin & Operations Control Plane

- **Status:** Accepted
- **Date:** 2026-08-12
- **Owner:** @atoz/lead, @atoz/governance
- **Documents affected:** 01-folder-structure.md, 05-api-flow.md,
  07-security-boundaries.md, 11-database-architecture.md, 12-api-contracts.md,
  13-ui-ux-design-system.md, 14-implementation-roadmap.md

## Context

M9 is the operations milestone. It must turn the admin surface into a real
production control plane: RBAC hardening, an append-only audit trail,
an operations dashboard (system health, queues, jobs, failures), unified
visibility across CMS/Affiliate/Pinterest/SEO/Analytics/Automation,
operational tools (searchable logs, webhook failure records, safe retries,
isolation verification, exports), notifications, and internal event
ingestion — all inside the Website Architecture Contract, with strict niche
tenancy, no cross-account leakage, and zero AI functionality.

The Database Blueprint (§5.17–§5.26) defines identity/RBAC tables
(`admin_users`, `roles`, `permissions`, `role_permissions`, `user_roles`,
`api_keys`), governance tables (`admin_preferences`, `audit_logs`,
`notifications*`), and platform tables (`queue_items`, `webhook_logs`,
`operation_logs`, `scheduled_jobs`, `job_runs`). API Contracts define the
Admin API auth model (JWT RBAC + MFA for privileged actions, revocable
sessions) and the eventing model (HMAC-signed webhooks with
`(source, event_id)` idempotency). Service ownership, the tenancy
transport for a *global* admin surface, the append-only enforcement point,
the seed policy for system roles, and the webhook ingestion surface were
unspecified, so this ADR freezes those decisions.

## Decision

### 1. `services/admin-service` owns the admin database (`admin_db`)

- The admin module gets its own Alembic migration stream
  (`services/admin-service/db/migrations/`), revision `0001`, with its own
  version table (`alembic_version_admin`) so the content, affiliate,
  Pinterest, SEO, analytics, and admin streams apply to the same physical
  database without interfering (same policy as ADR-0005/0006/0007/0008).
- `admin_db` holds only business data: local niche mirror, operator
  identity + RBAC reference rows, the append-only audit ledger,
  notifications, and the durable queue/webhook/operation/job records used
  by the control plane. No AI data lives here.
- CI validates the admin migration stream against the same fresh
  PostgreSQL 16 used by the other services, including downgrade/re-upgrade.

### 2. Tenancy for a global admin surface

- Global reference tables (`roles`, `permissions`) carry no `niche_id`.
- Every scoped record (`user_roles`, `api_keys`, `audit_logs`,
  `notifications`, `queue_items`, `webhook_logs`, `operation_logs`,
  `scheduled_jobs`, `job_runs`) carries an optional `niche_id`.
- The admin API accepts an optional `X-Niche-Id` header. When present, all
  scoped reads and writes are filtered server-side to that niche; when
  absent, the caller sees the global/aggregate view (super-admin surface).
  Cross-niche leakage is tested explicitly, and `/api/v1/admin/ops/isolation`
  verifies no scoped record references an unregistered niche.
- Cross-database foreign keys to `content_db.niches` are impossible, so
  `admin_db` keeps its own minimal `admin_niches` mirror (mirror policy,
  same as ADR-0005–0008).

### 3. Append-only audit ledger

- `audit_logs` is write-once: rows are created by the service layer on
  every privileged mutation and never updated or deleted. The repository
  exposes no update/delete paths, and the API surface exposes none
  (verified by tests asserting 404/405 for update/delete verbs).
- Audit records capture actor (operator or API key), action, resource
  (entity type/id), niche scope, request ID, and IP hash. Exports are
  capped by `audit_export_max_rows` (export control).

### 4. RBAC seed policy and MFA gating

- The frozen permission catalog and system-role matrix live in
  `domain/roles.py` and are seeded idempotently on startup (roles and
  grants are upserted; membership is operator-managed).
- Admin API routes enforce JWT RBAC server-side (`admin:read` for reads,
  `admin:write` for privileged actions). Privileged actions additionally
  require an MFA-verified session (`MFA_REQUIRED` otherwise). Sessions are
  revocable; in-memory in dev/CI, Redis-backed in production.

### 5. Operations dashboard and operational tools

- `/api/v1/admin/ops/status` probes sibling business services through
  `service_health_urls` (admin-service owns no cross-service knowledge
  beyond health URLs; business data always comes from the owning service).
- Queue/webhook/operation/job visibility is read-only for `admin:read`;
  retries are restricted to failed queue items below their attempt cap and
  require `admin:write` + MFA. Exports are capped.

### 6. Internal event ingestion

- `/api/v1/admin/events/ingest` consumes signed domain events from the
  business services (HMAC-SHA256 over the raw request body, same
  convention as the analytics webhook) and records them idempotently on
  `(source, event_id)`. Events map to operation records for the control
  plane only — no business mutation, no AI logic.

### 7. Frontend

- New admin pages (`/ops`, `/ops/logs`, `/audit`) are server components
  over the shared design system and render real admin API data when
  `NEXT_PUBLIC_ADMIN_API_BASE_URL` is configured, falling back to mock
  fixtures otherwise. All admin pages stay `noindex`.

## Consequences

- The admin surface becomes a governed control plane: privileged actions
  are audited and MFA-gated, scoped queries cannot leak across niches,
  and failures are searchable and safely retryable.
- The admin service stays a business layer: it consumes signed business
  events but never produces AI output, never calls LLM APIs, and never
  duplicates AI OS functionality.
- Future automation (Phase 12) and production operations (Phase 13) build
  on these frozen surfaces instead of inventing new ones.

## Contract compliance

- **No AI duplication:** the admin service contains no intelligence; the
  no-AI CI guard scans it and `pip-audit` blocks AI SDKs. It never calls
  OpenAI/Gemini/Claude, never runs prompts, embeddings, or inference, and
  never owns AI memory or learning.
- **Business layer only:** the service records, reports, and governs
  business operations (RBAC, audit, queues, webhooks, notifications).
  AI OS communication is exclusively through `services/aios-bridge` and
  `libs/contracts/aios`.
- **Website Architecture Contract:** boundaries are enforced by
  `/api/v1/admin/ops/isolation`, RBAC tests, audit immutability tests,
  webhook signature tests, and the 10-account isolation guarantees that
  remain owned by the Pinterest service.
