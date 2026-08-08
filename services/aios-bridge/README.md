# aios-bridge

**The ONLY AI OS contact point in the business layer** (Website Architecture
Contract §4.2, Folder Blueprint §5, API Contracts §12).

- **Owner:** `@atoz/bridge`
- **Status:** M3 skeleton — transport only, no business logic.

## What lives here

| Module | Purpose |
|--------|---------|
| `adapters/` | HMAC-SHA256 transport signing/verification (`X-AIOS-Signature`, timestamp, nonce) |
| `jobs/` | Retry policy (exp backoff 1s × 2, cap 60s, max 5) and circuit breaker (50%/60s) |
| `api/` | Bridge status + future inbound webhook receivers (Phase 4+) |
| `client.py` | `AiosBridgeClient` — validates contracts, signs, retries, heartbeats |
| `contracts.py` | JSON Schema validation against `libs/contracts/aios/` (frozen v1) |

## Hard boundary (never broken)

- No prompts, models, generation, learning, memory, routing, or LLM calls —
  ever. The bridge moves approved messages only.
- No other service or app may contact the AI OS, hold AI OS credentials, or
  import AI OS SDKs (enforced by `tools/dev/check-no-ai.sh`).
- The AI OS is reached only through this service and the contracts in
  `libs/contracts/aios/`.
