# atoz-backend-core

Shared backend foundation for the AtozProductHub business layer (ADR-0003).
Package: `atoz-backend-core`. Infrastructure primitives only — **no business
logic and no AI behavior**.

## Modules

| Module | Purpose |
|--------|---------|
| `config` | pydantic-settings base configuration (env loading, CORS, rate limits, OTel hooks) |
| `logging` | structured JSON logging with request-ID correlation |
| `middleware` | request ID, security headers, rate limiting (429 + Retry-After) |
| `db` | async PostgreSQL/Redis engines, session factory, health checks, ORM `Base` |
| `migrations` | per-service Alembic environment template (see `migrations/`) |
| `repositories` | repository pattern + unit of work (CRUD interfaces, transactions) |
| `events` | domain event envelope (`type.v1`), bus (in-memory / Redis pub-sub), publisher |
| `workers` | Celery app factory and base task (skeleton) |
| `auth` | JWT access/refresh tokens, RBAC, sessions, Argon2 password hashing, MFA placeholders |
| `security` | secrets loading (env + Vault KV v2 hooks) |
| `observability` | Prometheus metrics, OpenTelemetry hooks (no-op unless enabled) |
| `app` | `create_service_app` — shared FastAPI factory (`/health`, `/ready`, `/metrics`) |

## Boundaries

- Never imports apps, services, contracts, or the AI OS.
- Never contains business rules, domain entities, or AI generation/learning.
- Consumed by `apps/api` and every `services/*`; editable install order is
  backend-core first, then consumers.
