#!/usr/bin/env bash
# No-AI & forbidden-content guard.
# Enforces: Folder Blueprint §6.1 (forbidden folder names) and
# Website Architecture Contract §4.2 (no AI machinery in the business layer).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

FORBIDDEN_DIRS="ai ml models prompts training inference llm router memory research generation datasets weights agent"
FORBIDDEN_DEPS="openai anthropic google-generativeai langchain langgraph llama-index transformers torch tensorflow keras chromadb weaviate-client qdrant-client pgvector sentence-transformers ollama groq mistralai cohere"

violations=0

# 1. Forbidden folder names inside implementation trees
while IFS= read -r d; do
  base="$(basename "$d")"
  for f in $FORBIDDEN_DIRS; do
    if [ "$base" = "$f" ]; then
      echo "FAIL: forbidden folder '$d' (matches '$f')"
      violations=$((violations + 1))
    fi
  done
done < <(find apps services libs tools infra config -type d 2>/dev/null)

# 2. Forbidden dependencies in manifests
for manifest in pyproject.toml package.json apps/*/pyproject.toml apps/*/package.json services/*/pyproject.toml; do
  [ -f "$manifest" ] || continue
  for dep in $FORBIDDEN_DEPS; do
    if grep -Eq "(^|[^a-z])${dep}[>=<\"' ]" "$manifest"; then
      echo "FAIL: forbidden dependency '$dep' in $manifest"
      violations=$((violations + 1))
    fi
  done
done

if [ "$violations" -gt 0 ]; then
  echo "No-AI guard failed with $violations violation(s)."
  exit 1
fi
echo "No-AI guard: OK"
