# ADR-0005 — Affiliate Service Owns the Affiliate Business Layer

- **Status:** Accepted
- **Date:** 2026-08-10
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 01-folder-structure.md, 11-database-architecture.md, 12-api-contracts.md, 14-implementation-roadmap.md

## Context

M5 (affiliate business layer) is the monetization milestone. It must deliver
the affiliate network abstraction, merchant/product/offer records, affiliate
link and token management, a server-controlled signed redirector, click and
conversion ledgers, commission webhook ingestion with signature verification
and idempotency, commission lifecycle (pending → approved → paid / rejected),
revenue attribution, disclosure enforcement, admin management screens, and
public product/collection pages — while keeping niche tenancy (every business
record scoped by `niche_id`), the Website Architecture Contract, the M4 CMS
integration, and the M1–M3 foundations intact.

The Database Blueprint (§5.8–5.13) and API Contracts (§10–11) define the
tables and endpoints but leave service ownership, tenancy transport, redirect
security, ledger semantics, webhook idempotency, and disclosure enforcement
unspecified, so this ADR freezes those decisions.

## Decision

### 1. `services/affiliate-service` owns the affiliate database (`affiliate_db`)

- The affiliate module gets its own schema and its own Alembic migration
  stream (`services/affiliate-service/db/migrations/`), revision `0001`.
- Each service owns a distinct Alembic version table
  (`alembic_version_affiliate`, `alembic_version_content`) so both streams
  can be applied to the same physical database without one no-op'ing on the
  other's revision row.
- `affiliate_db` contains only business data: local niche mirror, networks,
  merchants, products, product categories, links, link tokens, clicks,
  attributions, revenue transactions, reconciliations, revenue summaries,
  and webhook logs. No AI OS data lives here.
- The service runs its own migrations; CI validates both content and
  affiliate migration streams against the same fresh PostgreSQL 16 database.

### 2. Local tenancy mirror instead of cross-database FKs (ADR-0004 §4)

- Every affiliate business record carries `niche_id` (Database Blueprint §4).
- Cross-database foreign keys from `affiliate_db` to `content_db.niches` are
  impossible in PostgreSQL, so `affiliate_db` keeps its own minimal
  `affiliate_niches` mirror (slug + name + status). The gateway keeps the
  niche registry in sync; the mirror is read-only inside the affiliate
  service and never authoritative.
- Tenancy transport matches ADR-0004: the public API identifies the niche by
  slug (`?niche=`), the admin API by the mandatory `X-Niche-Id` header, and
  every repository query and mutation is niche-scoped server-side.
- Networks and merchants are global reference tables (not niche-scoped);
  products, categories, links, tokens, clicks, and revenue records are
  niche-scoped. Pinterest account scope is not introduced in M5; attribution
  fields remain nullable for the future Pinterest milestone.

### 3. Server-controlled signed redirects

- Redirect identifiers are HMAC-signed tokens (`link_tokens`) created by the
  service and resolved only through the server endpoint
  `GET /api/v1/public/go/{signed}` (API Contracts §4 redirector).
- The browser never supplies a raw destination URL. The endpoint verifies the
  token signature, checks the link status (disabled/expired/revoked tokens
  return an indistinguishable 404), records the click in the append-only
  ledger before redirecting, and only then returns the stored
  `network_link_url` as JSON. Open redirects are prevented by construction.
- Network credentials never leave the service; the frontend only ever holds
  the signed token path.

### 4. Append-only ledgers

- `affiliate_clicks` and `revenue_transactions` are append-only: the
  repository layer exposes no update or delete paths. Commission status
  transitions are explicit `transition_commission` domain operations that
  write the new status onto the immutable row (rejected and paid are
  terminal; approved is the only path to paid). Reconciliation rows are
  also append-only records of each report run.
- Monetary values are integer cents with a `currency` column (Database
  Blueprint §5.10); server-side limits (`max_commission_cents`,
  `max_gross_cents`) reject out-of-range webhook amounts.

### 5. Webhook signature verification and idempotent ingestion

- Conversion webhooks arrive at `POST /webhooks/v1/{network_code}/conversion`
  with a raw body and `X-Webhook-Signature`. The service verifies the
  network-specific HMAC secret (dev defaults; production via Vault), validates
  the payload schema, and rejects invalid signatures/payloads with RFC7807
  problem+json (400) without touching the database.
- Every accepted delivery is logged to `affiliate_webhook_logs` keyed by
  `(source, event_id)`; repeated delivery of the same event is recorded as a
  duplicate and acknowledged with 202 (fast-ack, never an error).
- Conversions are keyed by `UNIQUE (network_id, network_transaction_id)` —
  the hard idempotency guarantee. The whole processing transaction rolls
  back on a unique-violation race and returns `(None, duplicate=True)`, so
  repeated webhook delivery can never create duplicate commission records.
- `revenue:attributed.v1` and `affiliate:click.v1` domain events are emitted
  after the transaction commits (ADR-0003 event system).

### 6. Disclosure enforcement in the business layer

- Disclosure text is static, curated copy (never AI-generated).
- A product cannot be activated without at least one active affiliate link
  carrying `disclosure_required=true` for the same niche (`_require_disclosure_links`).
- The public product/collection pages render the disclosure badge whenever
  the business layer marks the record; the affiliate CTA uses
  `rel="sponsored nofollow"` per the SEO contract.

### 7. UUIDv7 identifiers and deferred partitioning

- All primary keys are UUIDv7 (`domain/uuids.py`, shared via
  `atoz_backend_core` and re-exported by content-service) for time-ordered,
  index-friendly keys.
- Partitioning by niche/date is deferred until traffic volumes demand it
  (same policy as ADR-0004 §5); every high-volume table keeps its
  `niche_id` index so partitioning remains a pure migration.

## Consequences

- The affiliate module is a self-contained business service: it depends only
  on `atoz-backend-core`, SQLAlchemy, Alembic, and the standard library — no
  AI SDKs, no cross-service imports, no direct AI OS calls.
- Click/conversion/revenue correctness is enforced at the database level
  (unique constraints) and the service level (signature checks, idempotency,
  lifecycle state machine), with explicit cross-niche isolation tests.
- Public readers and admin operators share the same tenancy rules; the
  `apps/web` product/collection pages and `apps/admin` affiliate screens are
  wired through the typed clients when the affiliate API base is set, and
  fall back to mock fixtures otherwise (default CI build mode).
- Network adapters and production feed ingestion remain follow-ups: M5
  delivers the catalog/link/ledger business layer, webhook ingestion for the
  first networks, and reconciliation records — not outbound feed automation.

## Contract compliance

- **No AI duplication:** the affiliate service contains no research, product
  recommendation intelligence, selection, generation, learning, memory,
  prompt, router, model, or LLM code; the no-AI CI guard scans it like every
  tree, and `pip-audit` blocks AI SDKs in the dependency tree.
- **Business layer only:** the service implements business use cases only;
  intelligence (e.g. product selection) belongs to the AI OS and enters the
  website only through the AI OS Bridge.
- **Tenancy:** every applicable business object is niche-scoped; no
  cross-niche data leakage is possible, and isolation is covered by
  repository, service, and HTTP-level tests.
- **Redirect security:** server-controlled signed resolution only; raw
  browser-supplied destinations are never trusted.
