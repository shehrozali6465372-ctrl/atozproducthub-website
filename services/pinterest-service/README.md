# pinterest-service

Pinterest business layer: 10+ independent Pinterest accounts per niche,
OAuth 2.0 authorization-code connect, boards/sections, queue-based pin
publishing, per-account rate limits, publishing-attempt ledger, and
per-account analytics storage — M6 (ADR-0006).

- **Owner:** @atoz/pinterest
- **Status:** M6 complete — business layer implemented and tested; no AI
  functionality anywhere in this package.
- **Endpoints:** `/health`, `/ready`, `/metrics` (shared backend-core
  factory); `/api/v1/public/*` (read-only, by niche slug); `/api/v1/admin/*`
  (JWT RBAC `pinterest:read`/`pinterest:write` + mandatory `X-Niche-Id`);
  `/oauth/callback` (Pinterest redirect, state/CSRF verified).
- **DB migrations:** `db/migrations/` — own Alembic stream on `pinterest_db`
  (`alembic_version_pinterest`), validated against fresh PostgreSQL in CI.
- **Secrets:** token VALUES never enter the database; `pinterest_tokens`
  stores only a `vault_ref` (Vault boundary). Dev/test resolvers read
  `PINTEREST_TOKEN_<ACCOUNT_ID>` / `PINTEREST_OAUTH_CLIENT_SECRET` env vars;
  production requires the Platform Vault hook.
- **Rate limits:** per-account token buckets by Pinterest's `org_read` /
  `org_write` categories — one account's throttle never blocks another.
- **AI OS boundary:** this service never contacts the AI OS directly and
  never calls any LLM/model API; pin assets and copy arrive pre-authored
  from the AI OS workflow via the AI OS Bridge and are stored as business
  data.
