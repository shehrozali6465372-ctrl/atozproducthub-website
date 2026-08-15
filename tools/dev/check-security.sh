#!/usr/bin/env bash
# Security validation guard (Task 24 / M11 Phase 3, ADR-0014).
#
# Runs in CI alongside gitleaks and pip-audit:
#   * scans tracked source/config files for high-entropy secret patterns
#   * rejects tracked .env files (only .env.example is allowed)
#   * verifies staging/prod templates use placeholders, never real secrets
#   * runs npm audit (production deps, high/critical gates) when npm and a
#     lockfile are available
#   * confirms every security/guard artifact exists and parses
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

violations=0

fail() { echo "FAIL: $1"; violations=$((violations + 1)); }

# 1. Tracked secret files -----------------------------------------------------
tracked_env="$(git ls-files | grep -E '(^|/)\.env($|\.)' | grep -v '\.env\.example$' || true)"
if [ -n "$tracked_env" ]; then
  fail "tracked env files are not allowed: ${tracked_env}"
fi

# 2. Secret patterns in tracked source/config files ---------------------------
python3 - <<'PY'
import re
import subprocess
import sys

tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
patterns = [
    (re.compile(r"\b(?:sk|rk|ghp|gho|ghs|ghu)_[A-Za-z0-9]{20,}\b"), "API/private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private key block"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b"), "JWT-like token"),
]
violations = 0
for path in tracked:
    if "/node_modules/" in path or path.endswith((".lock", ".min.js", ".map", ".png", ".jpg")):
        continue
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        continue
    for pattern, label in patterns:
        if pattern.search(text):
            print(f"FAIL: {label} pattern found in {path}")
            violations += 1
sys.exit(1 if violations else 0)
PY
status=$?
violations=$((violations + status))

# 3. Template placeholders -----------------------------------------------------
for template in config/staging/env.template config/prod/env.template; do
  if ! grep -q "CHANGE_ME" "$template"; then
    fail "$template must keep secret values as CHANGE_ME placeholders"
  fi
done

# 4. npm audit (production deps, high/critical) --------------------------------
if [ -f package-lock.json ] && command -v npm >/dev/null 2>&1; then
  echo "== npm audit (production deps) =="
  if ! npm audit --omit=dev --audit-level=high; then
    fail "npm audit found high/critical vulnerabilities"
  fi
fi

# 5. Guard/security artifacts ----------------------------------------------------
for artifact in \
  tools/dev/check-no-ai.sh \
  tools/dev/check-contracts.sh \
  tools/dev/check-infra.sh \
  tools/dev/check-staging.sh \
  tools/observability/check-observability.sh \
  tools/db/validate-migrations.sh \
  tools/db/staging-recovery-drill.sh \
  tools/deploy/staging-smoke.sh \
  tools/deploy/rollback-test.sh; do
  if [ ! -x "$artifact" ]; then
    fail "guard artifact missing or not executable: $artifact"
  fi
done

if [ "$violations" -gt 0 ]; then
  echo "Security guard failed with ${violations} violation(s)."
  exit 1
fi
echo "Security guard: OK"
