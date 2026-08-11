# analytics-service — schema migrations

Alembic environment for the analytics database (`analytics_db`). The async
environment runs the same migrations against PostgreSQL (production/CI,
`postgresql+asyncpg://...`) and SQLite (migration tests,
`sqlite+aiosqlite:///...`). The analytics stream owns a distinct version
table (`alembic_version_analytics`) so content + affiliate + pinterest +
seo + analytics streams coexist on the same physical database (M5 fix).

## Running

```bash
# From the repository root (venv active):
cd services/analytics-service
DATABASE_URL=postgresql+asyncpg://atoz:atoz@localhost:5432/atoz \
  alembic -c db/migrations/alembic.ini upgrade head
```

## Current revision

- `0001_analytics_initial` — analytics_niches (tenancy mirror, ADR-0008),
  analytics_event_ledger (append-only, unique `event_id`),
  traffic_daily, visitor_daily, daily_metrics, kpi_snapshots. Every
  business record carries `niche_id`; Pinterest rows carry
  `pinterest_account_id`. The ClickHouse warehouse table
  (`analytics_events`) is infrastructure, created outside this stream.
