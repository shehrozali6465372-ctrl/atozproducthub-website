# 01 — Folder Structure

**Status:** Planned target layout. The repository remains documentation-only today; no implementation folder may be created until its scope and design document is approved (root `README.md`, Development Rules).

## 1. Current state

```
atozproducthub-website/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .gitignore
└── docs/
    └── architecture/        # This document set
```

## 2. Target structure (implementation phase)

```
atozproducthub-website/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .gitignore
├── docs/
│   ├── architecture/            # Architecture documentation (this set)
│   └── decisions/               # Architecture Decision Records (ADRs) — future
├── apps/
│   ├── web/                     # Public website — presentation only
│   ├── admin/                   # Admin dashboard — presentation only
│   └── api/                     # Business API gateway (routing, auth, webhooks)
├── services/
│   ├── content-service/         # Articles, publishing, content lifecycle
│   ├── pinterest-service/       # Pinterest accounts, boards, pins, scheduling
│   ├── affiliate-service/       # Product catalog, links, clicks, commissions
│   ├── seo-service/             # Metadata, sitemaps, structured data, SEO health
│   ├── analytics-service/       # Events, warehouse, metrics, reports
│   └── admin-service/           # Governance commands, audit log, settings
├── libs/
│   ├── contracts/               # OpenAPI / AsyncAPI schemas — the only shared code
│   └── domain-core/             # Pure value types and identifiers shared by contracts
├── infra/
│   ├── iac/                     # Infrastructure as code (environments, networking)
│   └── config/                  # Environment config and secrets references
├── pipelines/
│   └── ci/                      # CI/CD pipeline definitions
└── tests/
    ├── e2e/                     # End-to-end flows
    └── load/                    # Load and scale tests
```

## 3. Folder rules

1. **Apps are thin.** `apps/web`, `apps/admin`, and the future mobile client contain rendering and client behavior only. All business rules live in `services/`.
2. **Services own their data.** No service reads another service's database. Cross-service needs use contracts (`libs/contracts`) and events.
3. **Contracts are the only shared code.** `libs/domain-core` may contain pure identifiers and value types used in schemas. It never contains behavior.
4. **Infra is code.** Everything in `infra/` is declarative and reviewed like application code.
5. **No AI OS code.** Nothing in this repository may import, copy, or embed AI OS source. The AI OS is reached exclusively through the AI OS Bridge contract.
6. **Docs live with the repository.** Architecture changes are reviewed in `docs/` first, before any implementation folder is proposed.

## 4. Responsibility → folder mapping

| Responsibility | Primary location | Supporting location |
|----------------|------------------|---------------------|
| Website | `apps/web` | `services/content-service`, `services/seo-service` |
| Articles | `services/content-service` | `apps/web` (rendering), `services/seo-service` |
| Affiliate products | `services/affiliate-service` | `apps/web` (product pages) |
| Pinterest | `services/pinterest-service` | `services/analytics-service` (attribution) |
| SEO | `services/seo-service` | `apps/web` (tags), `services/content-service` |
| Traffic | `services/seo-service`, `services/analytics-service` | `apps/web` |
| Revenue | `services/affiliate-service` | `services/analytics-service` (reporting) |
| Analytics | `services/analytics-service` | `apps/admin` (dashboards) |
| Automation | `services/*` (workflows) + `pipelines/` | `apps/admin` (schedules) |
| Admin dashboard | `apps/admin` | `services/admin-service`, `services/analytics-service` |
| Future mobile app | future `apps/mobile` | `apps/api` (public read API), CDN |

## 5. What never appears in this repository

- AI OS source code, modules, prompts, or model artifacts.
- Generated content pipelines, model orchestration, or content intelligence.
- Shared databases between modules.
- Secrets, tokens, or keys in any form.
- Implementation folders without an approved scope/design document.
