# automation-service

Business automation workflows (scheduling, run history) — skeleton only (ADR-0002).

- **Owner:** @atoz/platform
- **Status:** M3 skeleton — infrastructure only, no business logic.
- **Endpoints:** `/health`, `/ready`, `/metrics` (shared backend-core factory).
- **DB migrations:** `db/migrations/` (populated in Phase 4).
- **AI OS boundary:** this service never contacts the AI OS directly; all AI OS
  communication flows through `services/aios-bridge/` and
  `libs/contracts/aios/`.
