# ADR-0006 — Pinterest Service Owns the Pinterest Business Layer

- **Status:** Accepted
- **Date:** 2026-08-10
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 01-folder-structure.md, 11-database-architecture.md, 12-api-contracts.md, 14-implementation-roadmap.md

## Context

M6 (Pinterest business layer) is the traffic milestone. It must deliver
independent Pinterest account management (10 accounts per niche, with strict
`pinterest_account_id` isolation), OAuth 2.0 authorization-code connect with
PKCE and per-account state/CSRF protection, a typed Pinterest API v5 client
(boards, board sections, pins) with per-account rate limits, queue-based pin
publishing with idempotency and retry, per-account publishing-attempt and
analytics records, an admin management UI, read-only public pages, and strict
adherence to the Website Architecture Contract — while keeping niche tenancy,
the M4 CMS and M5 affiliate integrations, and the M1–M3 foundations intact.

The Database Blueprint (§5.2–5.4) and API Contracts (§8.5) define the tables
and OAuth flow but leave service ownership, token storage, tenancy transport,
rate-limit isolation, queue semantics, and the AI OS boundary unspecified, so
this ADR freezes those decisions.

## Decision

### 1. `services/pinterest-service` owns the Pinterest database (`pinterest_db`)

- The Pinterest module gets its own schema and its own Alembic migration
  stream (`services/pinterest-service/db/migrations/`), revision `0001`.
- It uses its own Alembic version table (`alembic_version_pinterest`) so the
  content, affiliate, and Pinterest streams apply to the same physical
  database without one no-op'ing on another's revision row (same policy as
  ADR-0005 §1).
- `pinterest_db` contains only business data: local niche mirror, accounts,
  token records (Vault references only — never token VALUES), boards, board
  sections, pins, pin queue items, publishing attempts, and per-account
  analytics. No AI OS data lives here.
- CI validates the Pinterest migration stream against the same fresh
  PostgreSQL 16 used for content and affiliate.

### 2. Local tenancy mirror and dual tenancy scope

- Every account-scoped Pinterest record carries `niche_id` AND
  `pinterest_account_id` (Database Blueprint §4 mandatory rules); boards,
  pins, queue items, attempts, and analytics are never addressable without
  both.
- Cross-database foreign keys from `pinterest_db` to `content_db.niches` are
  impossible in PostgreSQL, so `pinterest_db` keeps its own minimal
  `pinterest_niches` mirror (slug + name + status), read-only inside the
  service and never authoritative.
- Tenancy transport matches ADR-0004/0005: the public API identifies the
  niche by slug (`?niche=`), the admin API by the mandatory `X-Niche-Id`
  header, and every repository query and mutation is account-scoped
  server-side; account-scoped queries without account context raise
  `AccountIsolationError`.

### 3. Token VALUES never enter the database

- `pinterest_tokens` stores only a `vault_ref`, scopes, status, and expiry
  metadata (Database Blueprint §5.2). Access/refresh token VALUES live behind
  the Vault boundary (`TokenVault`); the dev/test `InMemoryTokenVault` and
  `EnvSecretResolver` are placeholders until the Platform Vault hook is
  provisioned (production resolvers raise `ServiceUnavailableError`).
- Tokens are never returned by any API response and never logged.

### 4. OAuth 2.0 authorization-code flow with PKCE and state/CSRF

- `GET /oauth/authorize` is a service operation, not a browser route: the
  admin API starts the flow and returns a Pinterest authorization URL with a
  signed per-account state (`HMAC(state_secret, account_id)`), a PKCE
  `code_verifier`/S256 challenge, and only the minimal scopes
  (`boards:read`, `boards:write`, `pins:read`, `pins:write`).
- The callback verifies the state signature, compares it against the state
  stored on the account record (double CSRF binding), exchanges the code,
  stores the token payload in the Vault, and marks the account connected.
- Access tokens are refreshed automatically with a 60-second expiry margin;
  rotated refresh tokens are written back to the Vault; a failed refresh
  surfaces as a typed 401 so the client can raise it to the operator.

### 5. Per-account rate limiting (never a global queue)

- Pinterest documents `org_read` and `org_write` rate-limit categories; one
  account's throttle must never block the other nine.
- The typed client uses a token bucket per `(account_id, category)`
  (`PerAccountRateLimiter`) with exponential backoff + full jitter, honoring
  `Retry-After` on 429s, and a single 401-refresh-and-retry per request.
- Rate-limit status is recorded per account (`rate_limit_status`,
  `last_rate_limit_at`) and surfaced in the admin UI without exposing token
  material.

### 6. Queue-based publishing with idempotency and retry safety

- `pin_queue_items` is the durable scheduling source of truth (Redis holds
  only the working set). A pin moves `draft → queued → publishing →
  published` with `failed`/`cancelled` states; every attempt is recorded in
  the append-only `pin_publish_attempts` ledger.
- `UNIQUE (pinterest_pin_id)` on the queue plus the `enqueue_pin` duplicate
  check make scheduling idempotent; retries are restricted to safe operations
  (429/5xx/network) with a retry cap, and permanent failures (403/validation)
  mark the pin failed without further attempts.
- Only pre-authored assets and copy from the website/AI OS workflow are ever
  published — never third-party curated content.

### 7. Per-account analytics are business data only

- `pinterest_analytics` stores per-account daily metrics (impressions, saves,
  clicks, outbound clicks, engagement) as business data.
- No AI analytics engine exists here; AI OS insights remain read-only through
  the AI OS Bridge contracts.

### 8. Public layer is read-only

- `/api/v1/public/*` exposes only connected accounts, active boards, and
  published pins by niche slug; drafts, queues, token records, and internal
  states are never exposed.

### 9. No AI duplication

- The Pinterest service contains no research, generation, learning, memory,
  prompt, router, model, or LLM code; no LLM/model SDKs are imported anywhere
  in the package. Pin-generation intelligence belongs to the AI OS and enters
  the website only through the AI OS Bridge. The no-AI CI guard scans this
  tree like every other.

### 10. UUIDv7 identifiers and deferred partitioning

- All primary keys are UUIDv7 for time-ordered, index-friendly keys (same
  policy as ADR-0004 §5 / ADR-0005 §7).
- Partitioning of `pinterest_pins` / `pin_publish_attempts` by niche/date is
  deferred until traffic volumes demand it; the schema is partition-ready
  (tenancy columns + composite indexes) so partitioning stays a pure
  migration.

## Consequences

- The Pinterest module is a self-contained business service: it depends only
  on `atoz-backend-core`, FastAPI, SQLAlchemy, Alembic, httpx, and the
  standard library — no AI SDKs, no cross-service imports, no direct AI OS
  calls.
- Account isolation is enforced at the database level (composite unique
  constraints and per-account FKs) and the service level (mandatory
  `niche_id` + `pinterest_account_id` in every account-scoped query and
  mutation), with explicit 10-account and cross-account leakage tests.
- OAuth state, PKCE, Vault-bound token storage, and per-account rate limits
  are verified by unit, repository, service, and client tests against a mock
  Pinterest transport — no live Pinterest credentials are required in CI.
- Public readers and admin operators share the same tenancy rules; the
  `apps/web` landing page and `apps/admin` Pinterest screen are wired through
  typed clients when the Pinterest API base is set, and fall back to mock
  fixtures otherwise (default CI build mode).
- Real Pinterest access requires a live Pinterest app + authorized users;
  production connect is an operator action, and Pinterest Trial access is
  insufficient for production behavior (Trial pins are visible only to the
  creator). The `AIOS.Pinterest.Assets` gate, Pinterest Tag, and scheduler
  integration remain follow-ups.

## Contract compliance

- **No AI duplication:** the pinterest service contains no intelligence of
  any kind; the no-AI CI guard scans it and `pip-audit` blocks AI SDKs in the
  dependency tree.
- **Business layer only:** the service implements business use cases only
  (accounts, OAuth, boards, pins, queue, analytics storage); intelligence
  (pin design, copy, targeting) belongs to the AI OS and enters the website
  only through the AI OS Bridge.
- **Tenancy:** every account-scoped business object carries `niche_id` AND
  `pinterest_account_id`; cross-niche and cross-account leakage is impossible
  and covered by repository, service, and HTTP-level tests.
- **Secrets:** token VALUES never touch the database, responses, or logs;
  only Vault references and expiry metadata are stored.
