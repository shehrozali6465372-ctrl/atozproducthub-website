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


## UCOS Layer 23 integration

The Bridge targets the separate Universal Content Operating System repository.
Layer 23 (Website Manager) is the website-management execution surface.

- AtoZ -> services/aios-bridge -> UCOS /v1/jobs -> Layer 23.
- UCOS exposes /heartbeat for bridge liveness.
- Transport authentication uses the existing HMAC-SHA256 AIOS signing contract.
- No UCOS source is copied into this repository and no AtoZ source is copied into UCOS.
- Configure the AIOS base URL to the deployed UCOS gateway URL in staging/production; the local default is http://localhost:8000.
- The integration accepts real content and article identifiers only; it does not fabricate content, publishing results, analytics, or external platform IDs.
