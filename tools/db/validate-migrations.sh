#!/usr/bin/env bash
# Database migration stream validation (Task 24 / M11 Phase 3, ADR-0014).
#
# Modes:
#   validate  (default) — full staging/CI gate:
#       * exactly one head per service migration stream
#       * no migration-table collisions (distinct alembic_version_* tables)
#       * upgrade head on a fresh PostgreSQL database
#       * schema smoke checks (required tables exist)
#       * tenancy checks (niche_id columns on scoped business tables)
#       * critical unique/idempotency constraints exist
#       * downgrade base + re-upgrade (safe repeatable migrations)
#   upgrade   — deployment migration gate only: head check + upgrade head
#
# Requires PostgreSQL access via DATABASE_URL (asyncpg) for Alembic and
# PGHOST/PGPORT/PGUSER/PGDATABASE/PGPASSWORD for psql assertions.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

MODE="${1:-validate}"
case "$MODE" in
  validate|upgrade) ;;
  *) echo "usage: $0 [validate|upgrade]" >&2; exit 2 ;;
esac

: "${DATABASE_URL:?DATABASE_URL required (postgresql+asyncpg://...)}"
: "${PGPASSWORD:?PGPASSWORD required}"
: "${PGHOST:=localhost}"
: "${PGPORT:=5432}"
: "${PGUSER:=atoz}"
: "${PGDATABASE:=atoz}"

FAILURES=0

fail() { echo "FAIL: $1"; FAILURES=$((FAILURES + 1)); }

psql_check() { psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -tAc "$1"; }

# stream -> service dir -> required tables -> tenancy tables -> idempotency indexes
STREAMS=(
  "content"
  "affiliate"
  "pinterest"
  "seo"
  "analytics"
  "admin"
  "automation"
)

declare -A REQUIRED_TABLES
REQUIRED_TABLES[content]="niches articles article_versions categories article_categories tags article_tags"
REQUIRED_TABLES[affiliate]="affiliate_niches affiliate_networks affiliate_merchants affiliate_products product_categories product_category_links affiliate_links link_tokens affiliate_clicks click_attributions revenue_transactions revenue_reconciliations revenue_summaries affiliate_webhook_logs"
REQUIRED_TABLES[pinterest]="pinterest_niches pinterest_accounts pinterest_tokens pinterest_boards board_sections pinterest_pins pin_queue_items pin_publish_attempts pinterest_analytics"
REQUIRED_TABLES[seo]="seo_niches url_registry seo_metadata sitemap_shards seo_crawl_reports seo_health_checks"
REQUIRED_TABLES[analytics]="analytics_niches analytics_event_ledger traffic_daily visitor_daily daily_metrics kpi_snapshots"
REQUIRED_TABLES[admin]="admin_niches admin_users roles permissions role_permissions user_roles api_keys audit_logs notifications queue_items webhook_logs operation_logs scheduled_jobs job_runs"
REQUIRED_TABLES[automation]="automation_niches automation_rules automation_runs aios_job_records"

declare -A TENANCY_TABLES
TENANCY_TABLES[content]="articles categories tags"
TENANCY_TABLES[affiliate]="affiliate_products product_categories product_category_links affiliate_links link_tokens affiliate_clicks click_attributions revenue_transactions revenue_reconciliations revenue_summaries"
TENANCY_TABLES[pinterest]="pinterest_accounts pinterest_boards board_sections pinterest_pins pin_queue_items pin_publish_attempts pinterest_analytics"
TENANCY_TABLES[seo]="url_registry seo_metadata sitemap_shards seo_crawl_reports seo_health_checks"
TENANCY_TABLES[analytics]="analytics_event_ledger traffic_daily visitor_daily daily_metrics kpi_snapshots"
TENANCY_TABLES[admin]="audit_logs queue_items scheduled_jobs job_runs operation_logs notifications webhook_logs"
TENANCY_TABLES[automation]="automation_rules automation_runs aios_job_records"

declare -A IDEMPOTENCY_INDEXES
IDEMPOTENCY_INDEXES[content]="uq_articles_niche_slug uq_categories_niche_slug uq_tags_niche_slug uq_article_tags_article_tag"
IDEMPOTENCY_INDEXES[affiliate]="uq_affiliate_products_merchant_sku uq_product_categories_niche_slug uq_link_tokens_token uq_affiliate_webhook_source_event uq_revenue_summaries_niche_network_date"
IDEMPOTENCY_INDEXES[pinterest]="uq_pinterest_accounts_niche_name uq_pinterest_tokens_account uq_pin_queue_items_pin"
IDEMPOTENCY_INDEXES[seo]="uq_url_registry_niche_path uq_seo_metadata_url_registry"
IDEMPOTENCY_INDEXES[analytics]="ix_analytics_ledger_event_id"
IDEMPOTENCY_INDEXES[admin]="uq_admin_users_subject uq_admin_users_email uq_role_permission uq_user_role_niche uq_api_keys_key_hash uq_webhook_source_event uq_scheduled_job_key"
IDEMPOTENCY_INDEXES[automation]="uq_automation_rules_niche_code uq_automation_runs_idempotency uq_aios_job_record_job_contract"

echo "== migration stream validation (mode=${MODE}) =="

# 1. Version-table collisions ------------------------------------------------
version_tables="$(grep -rhoE 'alembic_version_[a-z]+' services/*/db/migrations/env.py | sort)"
duplicates="$(printf '%s\n' "$version_tables" | uniq -d)"
if [ -n "$duplicates" ]; then
  fail "duplicate migration version tables: $duplicates"
else
  echo "OK: migration version tables are unique ($(printf '%s' "$version_tables" | tr '\n' ' '))"
fi

# 2. Per-stream head / upgrade / schema / tenancy / downgrade -----------------
for stream in "${STREAMS[@]}"; do
  service_dir="services/${stream}-service"
  if [ ! -d "$service_dir/db/migrations" ]; then
    fail "missing migration directory for stream '${stream}'"
    continue
  fi

  heads="$(cd "$service_dir" && python -m alembic -c db/migrations/alembic.ini heads)"
  head_count="$(printf '%s\n' "$heads" | grep -c '(head)' || true)"
  if [ "$head_count" -ne 1 ]; then
    fail "stream '${stream}' has ${head_count} migration head(s); expected exactly 1"
  else
    echo "OK: ${stream} single migration head"
  fi

  (cd "$service_dir" && DATABASE_URL="$DATABASE_URL" \
    python -m alembic -c db/migrations/alembic.ini upgrade head)
  echo "OK: ${stream} upgrade head"

  if [ "$MODE" != "validate" ]; then
    continue
  fi

  for table in ${REQUIRED_TABLES[$stream]}; do
    present="$(psql_check "SELECT to_regclass('public.${table}') IS NOT NULL")"
    if [ "$present" != "t" ]; then
      fail "${stream}: required table '${table}' missing"
    fi
  done
  echo "OK: ${stream} schema smoke (${#REQUIRED_TABLES[$stream]} tables)"

  for table in ${TENANCY_TABLES[$stream]}; do
    has_niche="$(psql_check "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='${table}' AND column_name='niche_id')")"
    if [ "$has_niche" != "t" ]; then
      fail "${stream}: tenancy table '${table}' missing niche_id column"
    fi
  done
  echo "OK: ${stream} tenancy columns"

  for index_name in ${IDEMPOTENCY_INDEXES[$stream]}; do
    exists="$(psql_check "SELECT count(*) FROM pg_indexes WHERE indexname='${index_name}'")"
    if [ "$exists" != "1" ]; then
      fail "${stream}: critical unique/idempotency index '${index_name}' missing"
    fi
  done
  echo "OK: ${stream} unique/idempotency constraints"

  (cd "$service_dir" && DATABASE_URL="$DATABASE_URL" \
    python -m alembic -c db/migrations/alembic.ini downgrade base)
  (cd "$service_dir" && DATABASE_URL="$DATABASE_URL" \
    python -m alembic -c db/migrations/alembic.ini upgrade head)
  echo "OK: ${stream} downgrade base + re-upgrade"
done

if [ "$FAILURES" -gt 0 ]; then
  echo "Migration validation failed with ${FAILURES} violation(s)."
  exit 1
fi
echo "Migration validation: OK"
