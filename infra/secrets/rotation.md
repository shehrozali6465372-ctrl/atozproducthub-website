# Secret rotation policy (M11 Phase C)

References and procedure only — actual secret values live in Vault and are
injected by the deployment pipeline. No secret material belongs in this
repository (enforced by the backend-core production secrets guard and
gitleaks in CI).

## 1. Inventory

| Secret class | Vault path | Rotation cadence | Impact |
|---|---|---|---|
| JWT secrets (per service) | `secret/jwt/{service}` | 90 days | Refresh tokens reissued; sessions survive via refresh |
| Postgres/Redis/ClickHouse/Kafka credentials | `secret/stores/*` | 90 days | Rolling credential swap, dual-publish window |
| AI OS API key | `secret/aios/api-key` | 30 days | Bridge retries degrade; no data loss |
| Pinterest OAuth client secret + per-account tokens | `secret/pinterest/oauth/*` | 30 days | Per-account re-auth required |
| Affiliate webhook/token signing secrets | `secret/affiliate/*` | 90 days | Webhook signatures verify against old+new during window |
| Event-ingestion HMAC secrets | `secret/events/*` | 90 days | Producers/consumers must share the value; staged rollout |
| Admin internal token | `secret/admin/internal-token` | 30 days | Service-account calls fail until all sides rotate |

## 2. Rotation procedure

1. **Write new value** to Vault at the same path (KV v2 keeps old versions).
2. **Publish** the new value to the affected containers via a rolling
   restart; keep the old value accepted where verification is asymmetric
   (webhooks, HMAC) during a 24 h overlap window.
3. **Verify** health/readiness and a synthetic auth call before and after.
4. **Revoke** the old value after the overlap window and audit secret reads.

## 3. Dual-publish window

Secrets consumed by both sides (event HMAC, webhook secrets) rotate in two
phases: producers move first with both old+new accepted, consumers follow,
then old is revoked. This prevents a signature mismatch outage.

## 4. Incident rules

- On suspected compromise: rotate immediately (P0), revoke the leaked
  value, rotate dependent secrets (per-account Pinterest tokens, JWT
  secrets), and open an audit entry.
- Rotation must never block on a human step; the deployment workflow runs
  the same procedure for staging first.
