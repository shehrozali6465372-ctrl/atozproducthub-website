#!/usr/bin/env bash
# Deployment migration gate (Task 24 / M11 Phase 3, ADR-0014).
#
# Runs ``alembic upgrade head`` for every service migration stream inside a
# disposable compose container BEFORE the app rollout. Runs on the deploy
# host with the repo checked out and the target env file present.
#
# Usage (on the deploy host):
#   IMAGE_REPO=ghcr.io/<owner>/<repo> IMAGE_TAG=<sha> \
#     ENV_FILE=/opt/atozproducthub/.env.prod \
#     bash tools/deploy/run-migration-gate.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

: "${ENV_FILE:=.env.prod}"

# The gate must run inside the exact release images, so the pipeline
# generates the immutable image override first (tools/deploy/write-image-override.sh).
if [ ! -f infra/docker/compose.images.yml ]; then
  echo "FAIL: infra/docker/compose.images.yml not found" >&2
  echo "Run: IMAGE_REPO=... IMAGE_TAG=... bash tools/deploy/write-image-override.sh" >&2
  exit 2
fi

STREAMS=(
  content-service
  affiliate-service
  pinterest-service
  seo-service
  analytics-service
  admin-service
  automation-service
)

COMPOSE=(docker compose -f infra/docker/compose.prod.yml \
  -f infra/docker/compose.staging.yml \
  -f infra/docker/compose.images.yml \
  --env-file "$ENV_FILE")

for stream in "${STREAMS[@]}"; do
  echo "== migration gate: ${stream} =="
  "${COMPOSE[@]}" run --rm --no-deps "${stream}" \
    sh -c "cd /srv/services/${stream} && alembic -c db/migrations/alembic.ini upgrade head"
done

echo "Migration gate: OK"
