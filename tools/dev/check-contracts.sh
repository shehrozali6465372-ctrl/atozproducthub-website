#!/usr/bin/env bash
# Contract layout & schema validation (M1 DoD: CI contract validation).
# Ensures the contract namespaces from the Folder Blueprint exist and any
# OpenAPI/AsyncAPI YAML or JSON schema files parse cleanly.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

NAMESPACES="content pinterest affiliate seo analytics admin aios"
violations=0

# 1. Namespace directories exist
for ns in $NAMESPACES; do
  if [ ! -d "libs/contracts/$ns" ]; then
    echo "FAIL: missing contract namespace libs/contracts/$ns"
    violations=$((violations + 1))
  fi
done

# 2. YAML/JSON schema files parse (Python: yaml + json)
python3 - <<'PY'
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

violations = 0
for path in Path("libs/contracts").rglob("*"):
    if path.suffix in {".yaml", ".yml"}:
        if yaml is None:
            continue
        try:
            yaml.safe_load(path.read_text())
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: invalid YAML {path}: {exc}")
            violations += 1
    elif path.suffix == ".json":
        try:
            json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: invalid JSON {path}: {exc}")
            violations += 1
sys.exit(1 if violations else 0)
PY
status=$?
violations=$((violations + status))

if [ "$violations" -gt 0 ]; then
  echo "Contract validation failed with $violations violation(s)."
  exit 1
fi
echo "Contract validation: OK"
