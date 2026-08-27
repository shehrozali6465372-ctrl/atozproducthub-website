#!/usr/bin/env bash
# Staging live smoke suite (Task 24 / M11 Phase 3, ADR-0014).
#
# Fail-closed post-deploy verification. Two layers:
#   1. Edge checks against STAGING_BASE_URL (the API edge / Caddy):
#        /healthz 204, /health 200, /ready 200.
#   2. Host checks (when DOCKER=1 and the staging stack is local):
#        every required container is running and healthy via compose ps.
#
# Optional auth: STAGING_AUTH_TOKEN is sent as a Bearer token to admin
# endpoints when STAGING_ADMIN_CHECKS=1.
#
# Usage:
#   STAGING_BASE_URL=https://api.staging.atozproducthub.dev DOCKER=1 \
#     ENV_FILE=/opt/atozproducthub/.env.staging \
#     bash tools/deploy/staging-smoke.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

: "${STAGING_BASE_URL:?STAGING_BASE_URL required (e.g. https://api.staging.atozproducthub.dev)}"
: "${SMOKE_TIMEOUT:=10}"
: "${DOCKER:=0}"
: "${STAGING_AUTH_TOKEN:=}"
: "${STAGING_ADMIN_CHECKS:=0}"
: "${ENV_FILE:=}"

FAILURES=0

fail() { echo "FAIL: $1"; FAILURES=$((FAILURES + 1)); }
pass() { echo "OK: $1"; }

http_check() {
  local name="$1" expected="$2" url="$3"
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "$SMOKE_TIMEOUT" \
    -H "Authorization: Bearer ${STAGING_AUTH_TOKEN}" "$url" || true)"
  if [ "$code" = "$expected" ]; then
    pass "$name (${url})"
  else
    fail "$name: expected HTTP ${expected}, got ${code:-no-response} (${url})"
  fi
}

echo "== staging smoke: edge =="
http_check "edge healthz (204)" 204 "${STAGING_BASE_URL}/healthz"
http_check "edge health (200)" 200 "${STAGING_BASE_URL}/health"
http_check "edge ready (200)" 200 "${STAGING_BASE_URL}/ready"

if [ "$STAGING_ADMIN_CHECKS" = "1" ]; then
  : "${STAGING_AUTH_TOKEN:?STAGING_AUTH_TOKEN required when STAGING_ADMIN_CHECKS=1}"
  http_check "admin ops overview (200)" 200 "${STAGING_BASE_URL}/api/v1/admin/ops/overview"
  http_check "admin audit list (200)" 200 "${STAGING_BASE_URL}/api/v1/admin/audit?limit=5"
fi

if [ "$DOCKER" = "1" ]; then
  if ! command -v docker >/dev/null 2>&1; then
    fail "DOCKER=1 but docker is not installed"
  else
    COMPOSE=(docker compose -f infra/docker/compose.prod.yml -f infra/docker/compose.staging.yml)
    if [ -n "$ENV_FILE" ]; then
      COMPOSE+=(--env-file "$ENV_FILE")
    fi
    if ! "${COMPOSE[@]}" config -q >/dev/null 2>&1; then
      fail "staging compose profile does not validate"
    else
      pass "staging compose profile validates"
    fi
    REQUIRED=(
      proxy api aios-bridge content-service affiliate-service
      pinterest-service seo-service analytics-service admin-service
      automation-service automation-worker automation-beat
      postgres redis kafka clickhouse typesense
      otel-collector prometheus alertmanager grafana loki promtail
    )
    "${COMPOSE[@]}" ps >/dev/null 2>&1 || true
    for name in "${REQUIRED[@]}"; do
      state="$("${COMPOSE[@]}" ps --format '{{.Service}} {{.Status}}' | awk -v s="$name" '$1==s {$1=""; print}' | head -1)"
      case "$state" in
        *healthy*) pass "container ${name} healthy" ;;
        *)
          if [ -z "$state" ]; then
            fail "container ${name} not running"
          else
            fail "container ${name} not healthy: ${state}"
          fi
          ;;
      esac
    done
  fi
fi

if [ "$FAILURES" -gt 0 ]; then
  echo "Staging smoke failed with ${FAILURES} failure(s)."
  exit 1
fi
echo "Staging smoke: OK"
