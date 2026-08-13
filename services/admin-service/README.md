# admin-service

Admin & operations control plane (M9, v0.9.0): RBAC hardening, append-only
audit, operations dashboard, queue/webhook visibility, notifications, and
internal event ingestion.

- **Owner:** @atoz/governance
- **Status:** M9 — production control plane, business layer only.
- **Endpoints:**
  - `/health`, `/ready`, `/metrics` (shared backend-core factory)
  - `/api/v1/admin/roles|permissions|users` — RBAC catalog, operator identity
  - `/api/v1/admin/audit[/export]` — append-only, searchable, capped CSV export
  - `/api/v1/admin/ops/overview|status|isolation` — operations dashboard
  - `/api/v1/admin/queue[/{id}/retry]` — queue visibility + safe retry
  - `/api/v1/admin/logs/webhooks|operations` — searchable operational records
  - `/api/v1/admin/jobs|jobs/runs` — scheduled-job visibility
  - `/api/v1/admin/notifications*` — inbox + delivery preferences
  - `/api/v1/admin/mfa/provision`, `/sessions/{id}/revoke` — MFA/session controls
  - `/api/v1/admin/events/ingest` — HMAC-verified internal event ingestion
- **DB migrations:** `db/migrations/` — `admin_db` stream
  (`alembic_version_admin`), coexists with all sibling service streams.
- **Tenancy:** every scoped record carries `niche_id`; reads/writes filter
  server-side on the `X-Niche-Id` header; audit/queue/webhook/operation
  isolation is verified by `/api/v1/admin/ops/isolation`.
- **AI OS boundary:** this service never contacts the AI OS directly; all AI OS
  communication flows through `services/aios-bridge/` and
  `libs/contracts/aios/`. No AI functionality is implemented here.
