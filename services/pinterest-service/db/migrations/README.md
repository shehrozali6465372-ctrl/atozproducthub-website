# pinterest-service — schema migrations

Alembic environment for the Pinterest database (`pinterest_db`). The async
environment runs the same migrations against PostgreSQL (production/CI,
`postgresql+asyncpg://...`) and SQLite (migration tests,
`sqlite+aiosqlite:///...`).

## Running

```bash
# From the repository root (venv active):
cd services/pinterest-service
DATABASE_URL=postgresql+asyncpg://atoz:atoz@localhost:5432/atoz \
  alembic -c db/migrations/alembic.ini upgrade head
```

## Current revision

- `0001_pinterest_initial` — pinterest_niches (tenancy mirror, ADR-0006),
  pinterest_accounts, pinterest_tokens, pinterest_boards, board_sections,
  pinterest_pins, pin_queue_items, pin_publish_attempts,
  pinterest_analytics.

## Notes

- Strict Pinterest isolation (Database Blueprint §4): every account-scoped
  table carries `niche_id` AND `pinterest_account_id`; composite unique
  constraints prevent cross-account/cross-niche duplicates; the repository
  layer rejects account-scoped queries without account context.
- Token VALUES never live here: `pinterest_tokens` stores only a `vault_ref`
  (Vault), scopes, and expiry metadata (blueprint §5.2).
- `pinterest_pins` is an append-only ledger (blueprint §5.4): no delete
  path in the repository; remote deletions are state transitions.

## Deferred (later milestones)

- PostgreSQL LIST PARTITION BY `niche_id`/date for `pinterest_pins` and
  `pin_publish_attempts` (Database Blueprint §6) — schema is
  partition-ready (tenancy columns + indexes) but partitioning is applied in
  a later operational migration.
