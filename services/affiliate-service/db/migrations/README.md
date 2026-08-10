# affiliate-service — schema migrations

Alembic environment for the affiliate database (`affiliate_db`). The async
environment runs the same migrations against PostgreSQL (production/CI,
`postgresql+asyncpg://...`) and SQLite (migration tests,
`sqlite+aiosqlite:///...`).

## Running

```bash
# From the repository root (venv active):
cd services/affiliate-service
DATABASE_URL=postgresql+asyncpg://atoz:atoz@localhost:5432/atoz \
  alembic -c db/migrations/alembic.ini upgrade head
```

## Current revision

- `0001_affiliate_initial` — affiliate_niches (tenancy mirror, ADR-0005),
  affiliate_networks, affiliate_merchants, product_categories,
  affiliate_products, product_category_links, affiliate_links, link_tokens,
  click_attributions, affiliate_clicks, revenue_transactions,
  revenue_reconciliations, revenue_summaries, affiliate_webhook_logs.

## Notes

- No AI OS data lives here: product descriptions are referenced out-of-DB
  (`description_ref`) and every business record carries `niche_id`
  (Database Blueprint §4). Networks/merchants are global reference tables.
- `affiliate_clicks.revenue_transaction_id` is an ORM-level FK only (plain
  indexed column in DDL): the click↔transaction cycle cannot be a DDL
  constraint on SQLite; the enforced FK direction is
  `revenue_transactions.affiliate_click_id → affiliate_clicks.id`.

## Deferred (later milestones)

- PostgreSQL LIST PARTITION BY `niche_id` for catalogs/link tables
  (Database Blueprint §6) — schema is partition-ready (tenancy columns +
  indexes) but partitioning is applied in a later operational migration.
