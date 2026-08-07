# 10 — Technology Stack (Permanent Technology Specification)

**Status:** Frozen — binding for all future implementation
**Version:** 1.0
**Compliance:** Must always satisfy the [Website Architecture Contract](09-website-architecture-contract.md) and the [Folder Blueprint](01-folder-structure.md)

This document permanently fixes the complete technology stack of the business layer. Every technology is justified against five criteria: **Why selected, Why alternatives were rejected, Long-term scalability, Cost, Free tier availability, Production readiness.**

## 1. Guiding principles

1. **Business layer only.** Every technology below is general-purpose business software. Nothing in this stack generates, learns, researches, remembers, or routes intelligence — those capabilities belong exclusively to the AI OS.
2. **Website independence.** The stack is fully self-contained and operable without the AI OS. AI OS integration is limited to one contract surface: the AI OS Bridge (Section 12).
3. **Boring technology.** Proven, mainstream, well-documented tools with large talent pools.
4. **CDN-first and cache-first.** The stack favors static generation, caching, and edge delivery because the business serves millions of articles and pins.
5. **Cost-aware.** Free tiers and open-source options are preferred where production readiness allows; paid managed services are chosen only for operational leverage.
6. **Contract-first.** API style and validation are chosen to support the versioned contracts in `libs/contracts/`.

---

## 2. Frontend stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **Next.js (React)** — framework | Best-in-class SSR/SSG for SEO-first content; static generation and ISR map directly to the CDN-first architecture; one framework for the public site and the admin dashboard | Astro (weaker interactive-app story for admin), Nuxt/Vue (smaller ecosystem), Remix (weaker static content), plain React SPA (no SEO) | Millions of static pages via generation; edge rendering for dynamic bits; incremental builds | MIT, free | n/a (open source) | Battle-tested at very large scale |
| **shadcn/ui + Radix** — UI library | Copy-paste, own-the-code components; accessible primitives; zero lock-in; works with Tailwind | MUI (heavy, opinionated), Ant Design (admin-centric, less neutral), Chakra (less composable) | Grows with the design system without framework churn | MIT, free | n/a | Production-proven primitives |
| **Tailwind CSS** — styling | Utility-first tokens; compile-time CSS (no runtime); consistent theming across web and admin | CSS Modules (verbose), Sass (manual), styled-components (runtime cost, SSR complexity) | Scales with design tokens; small bundles | MIT, free | n/a | Extremely widely deployed |
| **TanStack Query + Zustand** — state | Server state (API/read models) cached and synchronized cleanly; tiny client state store | Redux Toolkit (boilerplate), Recoil/Jotai (smaller ecosystem), Context-only (insufficient for admin) | Cache-first reads match the architecture; server/client state separation scales | MIT, free | n/a | Very large community |
| **React Hook Form + Zod** — forms | Performant, minimal re-renders; Zod schema validation shared with contracts philosophy | Formik (older, more boilerplate), Final Form (smaller ecosystem) | Form schemas mirror contract schemas; low maintenance | MIT, free | n/a | Production-proven |
| **Recharts** — charts | Composable React-native charts; MIT; enough power for KPI dashboards | Chart.js (less React-native), D3 (too low-level), Tremor (newer, thinner ecosystem) | Fine for business KPIs; swap possible without architecture change | MIT, free | n/a | Very widely used |
| **Lucide** — icons | Clean, consistent, MIT; the default for the shadcn ecosystem | Font Awesome (licensing complexity), Heroicons (smaller set) | No licensing risk as the icon set grows | MIT, free | n/a | Production-proven |

## 3. Backend stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **FastAPI** — framework | Async Python, typed end-to-end, OpenAPI generation built-in — a perfect match for the contract-first architecture; one language across gateway and every service | Django (heavy, ORM-coupled, weaker async), Flask (sync, unstructured), Node/NestJS (second language across the monorepo) | Per-service deployment; async I/O for I/O-bound business services; partitions cleanly by bounded context | MIT, free | n/a | Very widely used in production |
| **REST + JSON (OpenAPI)** — API style | Simple, cacheable, CDN-friendly, webhook-friendly; schema-first contracts in `libs/contracts/` | GraphQL (caching complexity, poor fit for cache-first content), gRPC (better internally but weak webhook/external story) | Cache-friendly versioned surfaces; additive evolution | Free (spec) | n/a | Universal standard |
| **Pydantic v2** — validation | Native to FastAPI; schema-first validation that generates the OpenAPI contracts; Rust-core performance | Marshmallow (less typed), attrs (low-level) | Validates at the edge of every service; enforces contract compliance cheaply | MIT, free | n/a | Production-proven |
| **OIDC + JWT + MFA (WebAuthn/TOTP)** — authentication | Standard, provider-neutral identity; JWT for API access; MFA mandatory for admin | Session-only (poor API fit), homegrown JWT (security risk), API-key-only (insufficient for admin) | Roles/permissions scale via OIDC claims; identity providers are swappable | Free (standard); IdP cost optional | Free tiers at IdPs (e.g., Google, Entra ID) | Industry standard |
| **Celery + Redis (Beat)** — background jobs | Mature, battle-tested worker system; Redis broker; Beat for scheduled jobs (pins, sitemaps, reports) | RQ (fewer features), ARQ (younger), Temporal (powerful but heavy operations) | Per-account pin queues and partitioned job flows; horizontally scalable workers | BSD, free | n/a (Redis free tier at Upstash) | Decades of production use |

## 4. Database stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **PostgreSQL** — primary database | Transactional integrity for business data, JSONB for flexible fields, native partitioning (by niche/date), full-text search built-in, massive ecosystem | MySQL (weaker partitioning/JSONB), MongoDB (document model weaker for transactional business data), SQLite (not production scale), CockroachDB (ops-heavy) | Partitioning by niche/date, read replicas, connection pooling; the per-service schema ownership model scales cleanly | OSS free; managed cost optional | Managed free tiers (Neon, Supabase, RDS 12-month) | The most battle-tested open-source database |
| **Redis** — cache & queues | Fast cache, rate-limit counters, Celery broker, per-account pin queues | Memcached (no persistence/queues), Dragonfly (newer, less proven) | Cache-first reads; partitioned queue workers for pins/clicks | OSS free; managed cost optional | Upstash free tier | Production-proven everywhere |
| **Typesense** — search | Fast, typo-tolerant, low-ops; lexical/filtering search only — perfectly scoped for the business layer | Elasticsearch/OpenSearch (heavy ops, cost), Algolia (SaaS cost scales with records), Meilisearch (similar, smaller ecosystem) | Per-niche index shards; millions of documents; instant filtering | OSS free; cloud optional | OSS free; Algolia-type SaaS not required | Production-proven |
| **S3-compatible object storage (Cloudflare R2)** — file storage | Immutable content blobs, generated pin assets, sitemap artifacts; R2 has no egress fees and integrates with the CDN | Local disk (not scalable), database blobs (poor performance), AWS S3 alone (egress costs) | Unlimited capacity model; versioning for content safety | R2 free tier; S3-compatible means vendor-swappable | Cloudflare R2 free tier (10 GB) | Production-proven standard |

## 5. Infrastructure stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **Docker** — containers | Uniform packaging for every service; local dev parity via Compose (apps + services + PostgreSQL + Redis) | Bare metal (slow iteration), PaaS lock-in without containers (portability loss) | Images move to any runtime; per-service scaling | OSS free | n/a | Industry standard |
| **GitHub Actions** — CI/CD | Already the repository host; native, free for public repos, huge marketplace | GitLab CI (second platform), Jenkins (ops-heavy), CircleCI (costlier for private) | Reusable pipelines in `pipelines/ci/`; scheduled jobs for automation | Free for public; generous for private | Free minutes for public repos | Production-proven |
| **Vercel** — frontend hosting | First-class Next.js: CDN, ISR, preview deployments, edge — the exact CDN-first model | Netlify (weaker Next.js support), self-hosted Node (loses edge/CDN leverage) | Global CDN, instant static delivery, edge functions | Paid after Hobby | Generous Hobby tier | Production-proven at massive scale |
| **Fly.io** — backend hosting | Global containers, Docker-native, per-region scaling, predictable pricing | Railway (less global), Render (free tier spins down), raw Kubernetes (high ops for a solo platform) | Global regions near CDN; horizontal scaling of services and workers | Pay-as-you-go | Small monthly allowance | Production-proven |
| **Cloudflare** — CDN / WAF / DNS | DDoS protection, WAF, bot management, caching, DNS — free tier is genuinely useful; front of Vercel | AWS CloudFront (no WAF in free tier, egress costs), Imperva (expensive) | Edge caching and protection scale globally without app changes | Free tier + cheap paid plans | Strong free tier | Production-proven |
| **OpenTelemetry + Grafana stack (Loki, Prometheus, Tempo, Grafana)** — logging & monitoring | Open standard instrumentation; self-hostable, vendor-neutral; logs, metrics, traces in one platform | Datadog (very expensive), New Relic (costlier), ELK (heavier ops) | Metrics/logs/traces scale with partitioned pipelines; dashboards as code | OSS free; Grafana Cloud optional | Grafana Cloud free tier | Production-proven |

## 6. SEO stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **Next.js metadata + SSR/SSG** | Native title/description/canonical/OG output; static HTML for crawlers | Client-rendered SPA (crawlability risk), WordPress+plugins (not our stack) | Millions of pre-rendered URLs with incremental builds | Free | n/a | Production-proven |
| **seo-service sitemap sharding (FastAPI + object storage)** | Sitemaps generated as sharded artifacts (`sitemap-00001.xml.gz` …) and served from the CDN | Single sitemap file (breaks at 50k URLs), on-the-fly sitemap endpoints (load on crawlers) | Shards scale to millions of URLs; independent rebuild jobs | Free | n/a | Standard practice |
| **JSON-LD / schema.org structured data** | Standard structured data for articles, products, FAQ, breadcrumbs | Microdata/RDFa (older), proprietary markup (no ecosystem value) | Extensible schema set; validated in CI | Free | n/a | Industry standard |
| **Google Search Console + Bing Webmaster APIs** | Official crawl/index/performance data for health reporting | Scraping search engines (ToS violation), third-party rank trackers (unreliable) | Automated health reports in the admin dashboard | Free | Free | Official APIs |
| **Lighthouse CI + `web-vitals`** | Performance budgets and Core Web Vitals in CI and analytics | Manual testing (misses regressions), proprietary speed tools (less transparent) | Budgets gate releases; trends feed analytics | Free | Free | Production-proven |
| **Sharded robots + URL policy (seo-service)** | Explicit crawl rules per niche; canonical enforcement | Default robots (loses crawl control at scale) | Per-niche crawl policies; URL changes emit events | Free | n/a | Standard practice |

## 7. Pinterest stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **Pinterest API v5 (OAuth 2.0 per account)** | Official publishing/management API; one authorization per account supports 10+ accounts | Third-party schedulers (Tailwind/Later — SaaS cost, less control), scraping (against ToS) | Per-account tokens + rate-limit budgets; account-per-niche isolation | Free (API access) | Free | Official, production API |
| **Pinterest Tag** | Official conversion/click pixel for attribution and audience measurement | No pixel (no conversion data), GA4-only (loses Pinterest-native data) | Fires on article/product pages; feeds the analytics pipeline | Free | Free | Official |
| **Pinterest Insights API** | Official pin/account performance data pulled into analytics reports | Manual dashboard review (no scale), screenshots (fragile) | Scheduled pulls per account; metrics into the warehouse | Free | Free | Official |
| **Per-account token vault + Redis/Celery queues** | Tokens in the secrets vault; per-account publish queues with independent rate-limit budgets | Shared token (breaks per-account isolation), synchronous publishing (blocks on rate limits) | Adding an account is configuration, not architecture | Free | n/a | Standard practice |

**Boundary note:** pin *assets* (images/copy) are generated by the AI OS and delivered through the AI OS Bridge; this stack publishes, schedules, and measures them — it never generates them.

## 8. Affiliate stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **Network adapters (affiliate-service)** | One adapter per network behind a common catalog contract | A single fixed network SDK (lock-in), manual link management (no scale) | Adding networks is configuration; feeds/APIs normalize into one catalog | Free | n/a | Standard practice |
| **Self-hosted link redirector (signed tokens)** | Full control over attribution, dedupe, and abuse protection; `/go/{token}` pattern | SaaS link shorteners (lost data, cost), cloaking services (opaque, risky) | Click ledger scales by partition; token validation is cheap | Free | n/a | Standard practice |
| **Click & commission ledger (PostgreSQL)** | Transactional correctness for revenue; append-only click records | Spreadsheets (no scale/audit), SaaS-only reporting (no reconciliation control) | Partitioned by month/niche; nightly reconciliation | Free | Managed free tiers | Production-proven |
| **Network webhooks + nightly reconciliation** | Signed conversion callbacks plus scheduled report pulls for accuracy | Manual verification (misses events), trusting one source only (discrepancies) | Reconciliation jobs scale by network/niche | Free | n/a | Standard practice |
| **Disclosure templates (`assets/templates/` + web rendering)** | Mandatory affiliate disclosure enforced by templates, not discipline | Manual per-page disclosure (compliance risk) | Compliance inherited by every monetized page automatically | Free | n/a | Standard practice |

## 9. Analytics stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **First-party event collector (analytics-service)** | Full ownership of event schema, data, and privacy; per-niche partitioning | GA4 as the system of record (data ownership/privacy limits), third-party scripts (leak data) | Edge → collector → stream; request path never blocks on analytics | Free | n/a | Standard practice |
| **Apache Kafka** — event stream | Durable, replayable, partitionable stream for clicks, pins, metrics | Redis Streams (MVP-grade but weaker at very large scale), direct DB writes (lossy pipeline) | Partitioned consumers scale with event volume | OSS free; managed optional | Confluent Cloud free tier | Industry standard |
| **ClickHouse** — warehouse | Columnar analytics at millions-of-events scale; fast partitioned queries | BigQuery/Snowflake (SaaS cost scales), Postgres warehouse (slow analytical scans), DuckDB (embedded, not a service) | Day + niche partitions; read models served cheaply | OSS free; cloud optional | ClickHouse Cloud free tier | Production-proven at huge scale |
| **Grafana + Recharts** — dashboards | Grafana for operational/analytics exploration; Recharts for in-app KPI dashboards | Metabase (analytics-only, weaker embedding), SaaS BI (cost + lock-in) | Dashboards as code; read models via analytics-service APIs | OSS free | Grafana Cloud free tier | Production-proven |
| **Metric definitions as code** | KPIs defined, reviewed, and versioned like code in `analytics-service` | Ad-hoc SQL in dashboards (drift, no review) | Metrics evolve with contracts; consistent across surfaces | Free | n/a | Standard practice |

**Boundary note:** predictions, insights, and learning are AI OS work. Analytics provides measurements; the AI OS may return insights over the Bridge, displayed read-only.

## 10. Security stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **Cloudflare WAF / DDoS / bot management** | Edge protection before anything reaches compute; strong free tier | AWS WAF/Shield (paid, complex), self-built rate limiting only (insufficient) | Global edge protection without app changes | Free tier + cheap paid | Strong free tier | Production-proven |
| **HashiCorp Vault** — secrets | Industry-standard secrets manager: per-Pinterest-account tokens, API keys, DB credentials | `.env` files (leak risk), Infisical (lighter, viable later), cloud-native secret stores (lock-in) | Vault policies scale with services; rotation automation | OSS free; managed optional | HCP free tier for dev | Industry standard |
| **OIDC + MFA (WebAuthn/TOTP)** | Standard identity with MFA mandatory for admins; RBAC via claims | Password-only (unacceptable for admin), homegrown sessions (risk) | Roles/permissions via claims; IdP swappable | Free | IdP free tiers | Industry standard |
| **Trivy + Dependabot + gitleaks** — CI security | Container/dependency/secret scanning in CI; all open source | Snyk (cost), proprietary scanners (lock-in) | Scans every PR/release automatically | OSS free | Free | Production-proven |
| **CSP + security headers (Next.js/edge)** | Content-Security-Policy, HSTS, frame/clickjacking protection | Default headers (weak), middleware-only headers (incomplete coverage) | Enforced at the edge for every response | Free | n/a | Standard practice |
| **Rate limiting (Cloudflare + gateway)** | Edge limits plus gateway limits per key/token | Edge-only (coarse), app-only (origin exposure) | Per-niche/account/API-key budgets | Free | Free tier | Standard practice |

## 11. Admin dashboard stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **Next.js + shadcn/ui + Tailwind** | Same frontend stack as the website — one framework, two surfaces, shared conventions | Retool (SaaS lock-in, cost), separate framework (duplicate skills/bundles) | Admin reads scale via read models; no business logic in the UI | Free | n/a | Production-proven |
| **TanStack Query (read models)** | Dashboard data cached and refreshed cleanly from analytics/domain APIs | Redux (boilerplate), polling everywhere (no caching) | KPI pages reuse cached read models | Free | n/a | Production-proven |
| **Recharts (KPI dashboards)** | Revenue, SEO health, pin performance, analytics charts in-app | Embedded Metabase (look/feel split), D3 (too low-level) | Matches the analytics stack's read models | Free | n/a | Production-proven |
| **RBAC via OIDC claims + admin-service** | Permissions enforced server-side; UI reflects but never decides | UI-only permissions (bypassable), hardcoded roles (rigid) | Role matrix scales with modules; audit-logged | Free | n/a | Standard practice |
| **Append-only audit store** | Every admin action recorded immutably | No audit log (compliance risk), mutable logs (tampering risk) | Partitioned by month; retention policy | Free | n/a | Standard practice |

## 12. AI OS Bridge stack

| Technology | Why selected | Alternatives rejected | Long-term scalability | Cost | Free tier | Production readiness |
|------------|--------------|------------------------|------------------------|------|-----------|------------------------|
| **Dedicated bridge service (FastAPI)** | One deployable that owns all AI OS communication; enforceable, observable, auditable | Embedding AI OS clients in every service (violates the contract), gateway direct calls (bypasses the bridge) | New AI OS contracts land here only; other services stay clean | Free | n/a | Standard integration pattern |
| **Versioned contracts (`libs/contracts/aios/`, OpenAPI)** | Schema-first, reviewed contracts for intake/status/assets/insights | Ad-hoc payloads (drift), unversioned endpoints (breaking changes) | Contract evolution is additive; breaking changes versioned | Free | n/a | Standard practice |
| **mTLS + HMAC signatures** | Authenticated, non-repudiable transport between the two systems | Plain HTTPS only (weaker assurance), shared static token (rotates poorly) | Scales with job volume; replay protection | Free | n/a | Industry standard |
| **Tenacity (retries) + circuit breaker** | Resilience so the website never blocks on AI OS latency/failure | Infinite retries (queue pileups), no circuit breaking (cascading failures) | Degrades gracefully; backlog recovers via queues | MIT, free | n/a | Production-proven |
| **Vault-only credentials** | AI OS credentials exist only in the vault; bridge is the only consumer | Credentials in config/env files (leak risk) | Rotation and audit apply at one point | Free | n/a | Standard practice |

**Boundary note:** the bridge contains adapters, verification, mapping, and resilience only. It contains zero prompts, models, generation, learning, or memory. All intelligence stays in the AI OS repository.

## 13. Website independence & the AI OS boundary (technology level)

- **The stack is fully functional without the AI OS.** Every technology above is general-purpose business software.
- **The website communicates with the AI OS ONLY through the AI OS Bridge** (Section 12). No other component holds AI OS credentials or calls AI OS endpoints.
- **Forbidden technologies in this repository** (they belong to the AI OS): LangChain or similar agent frameworks; OpenAI/Anthropic/Google model SDKs; any LLM inference gateway; prompt systems or prompt files; model routers; vector/embedding databases (pgvector, Chroma, Weaviate, etc.); model weights/checkpoints; training or fine-tuning pipelines; semantic/content-generation services.
- **If the website ever needs a semantic or generated capability, it consumes it through a versioned Bridge contract** — it never installs the technology itself.
- **CI enforcement:** dependency scanning rejects any package in the forbidden categories; folder review rejects the forbidden names defined in the Folder Blueprint (§6.1).

## 14. Final stack table

| Technology | Purpose | Status | Future Replacement |
|------------|---------|--------|---------------------|
| Next.js (React) | Frontend framework (web + admin) | Frozen | None planned (Astro considered, rejected) |
| shadcn/ui + Radix | UI components | Frozen | None planned |
| Tailwind CSS | Styling | Frozen | None planned |
| TanStack Query + Zustand | State management | Frozen | None planned |
| React Hook Form + Zod | Forms & validation | Frozen | None planned |
| Recharts | Charts | Frozen | Tremor (if ecosystem matures) |
| Lucide | Icons | Frozen | None planned |
| FastAPI | Backend framework | Frozen | None planned |
| REST + JSON (OpenAPI) | API style | Frozen | gRPC internally, only with ADR |
| Pydantic v2 | Validation | Frozen | None planned |
| OIDC + JWT + MFA | Authentication | Frozen | Passkeys-only (as browsers mature) |
| Celery + Redis (Beat) | Background jobs | Frozen | Temporal (if workflows outgrow Celery) |
| PostgreSQL | Primary database | Frozen | None planned |
| Redis (Upstash) | Cache & queues | Frozen | Self-hosted Redis/Valkey |
| Typesense | Search (lexical) | Frozen | Algolia (managed, only if ops savings justify) |
| Cloudflare R2 (S3-compatible) | File storage | Frozen | Self-hosted MinIO or AWS S3 |
| Docker | Containers | Frozen | None planned |
| GitHub Actions | CI/CD | Frozen | Buildkite (only if scale demands) |
| Vercel | Frontend hosting | Frozen | Self-hosted Next.js on Fly.io |
| Fly.io | Backend hosting | Frozen | AWS ECS/Kubernetes (only with team growth) |
| Cloudflare | CDN / WAF / DNS | Frozen | AWS CloudFront (only if provider strategy changes) |
| OpenTelemetry + Grafana stack | Logging & monitoring | Frozen | Grafana Cloud (managed) or Datadog (only if budget allows) |
| Next.js metadata + SSG | SEO rendering | Frozen | None planned |
| seo-service sitemap sharding | Sitemaps & robots | Frozen | None planned |
| JSON-LD (schema.org) | Structured data | Frozen | None planned |
| GSC + Bing Webmaster APIs | Crawl health data | Frozen | None planned |
| Lighthouse CI + web-vitals | Performance budgets | Frozen | None planned |
| Pinterest API v5 | Pin publishing/management | Frozen | None planned |
| Pinterest Tag | Conversion tracking | Frozen | None planned |
| Pinterest Insights API | Pin performance data | Frozen | None planned |
| Affiliate network adapters | Product & commission feeds | Frozen | More networks as adapters |
| Self-hosted link redirector | Affiliate link attribution | Frozen | None planned |
| Click & commission ledger | Revenue tracking | Frozen | None planned |
| First-party event collector | Analytics collection | Frozen | None planned |
| Apache Kafka | Event stream | Frozen | Redpanda (single-binary ops) |
| ClickHouse | Analytics warehouse | Frozen | BigQuery (only at very large managed scale) |
| Grafana + Recharts | Dashboards | Frozen | None planned |
| Cloudflare WAF/DDoS/bot | Edge security | Frozen | None planned |
| HashiCorp Vault | Secrets | Frozen | Infisical (lighter self-hosted option) |
| Trivy + Dependabot + gitleaks | CI security scanning | Frozen | None planned |
| AI OS Bridge (FastAPI) | Sole AI OS integration point | Frozen | None planned (contract-mandated) |

## 15. Change process

- This specification is **frozen**. Any technology change requires an ADR in `docs/decisions/`, a contract-compliance review, a `CHANGELOG.md` entry, and approval by the Lead Software Architect.
- Proposed changes that introduce AI/LLM/model capabilities are rejected outright under the Website Architecture Contract §1 and §7.
