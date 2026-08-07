# AtozProductHub Website

> The business layer of AtozProductHub: a content-driven website for articles, affiliate products, Pinterest, SEO, traffic, revenue, analytics, automation, and the admin dashboard.

This repository is **exclusively** for the AtozProductHub website — the business layer. It is intentionally separate from the **Universal AI Content Operating System** (AI OS), which already exists and is maintained in its own repository.

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [Project Goals](#2-project-goals)
3. [Project Scope](#3-project-scope)
4. [Repository Rules](#4-repository-rules)
5. [Architecture Philosophy](#5-architecture-philosophy)
6. [Relationship with Universal AI Content Operating System](#6-relationship-with-universal-ai-content-operating-system)
7. ["No Duplicate Features" Policy](#7-no-duplicate-features-policy)
8. [Development Rules](#8-development-rules)
9. [Future Roadmap](#9-future-roadmap)
10. [Architecture](#architecture)

---

## 1. Project Vision

AtozProductHub aims to become a trusted, high-traffic product discovery and content platform that turns educational articles and curated affiliate product recommendations into sustainable revenue — powered by automation but owned by clear business logic.

The website is the face of the business: where readers land, where products are recommended, where traffic is captured, and where revenue is earned. The AI OS works behind the scenes; this website is what users see and interact with.

## 2. Project Goals

- Publish high-quality, SEO-optimized articles that attract organic traffic.
- Showcase and monetize curated affiliate products with full disclosure.
- Grow and automate a Pinterest-driven traffic channel.
- Capture, measure, and improve traffic, engagement, and revenue with analytics.
- Automate repetitive operational tasks without reinventing AI capabilities.
- Provide a clear, data-informed admin dashboard for business oversight.
- Keep the business layer simple, fast, secure, and maintainable.

## 3. Project Scope

### In Scope (this repository)

- Website and user-facing pages.
- Article publishing and content presentation.
- Affiliate product listings, linking, and disclosure.
- Pinterest integration (pins, boards, and traffic attribution).
- SEO implementation (metadata, sitemaps, structured data, performance).
- Traffic management and acquisition tooling.
- Revenue tracking and affiliate reporting.
- Analytics instrumentation and reporting.
- Business automation workflows.
- Admin dashboard for content, products, and business operations.

### Out of Scope (owned by the AI OS or other systems)

- AI content generation, model orchestration, or content intelligence.
- Any AI OS functionality, module, or pipeline — copied or reimplemented.
- The AI OS repository itself — it is never merged, copied, or forked here.

## 4. Repository Rules

- This repository contains **only** the website business layer.
- No AI OS code, files, or functionality may be imported, copied, or duplicated.
- No implementation code may be added until an approved scope/design doc exists.
- Keep documentation and code changes reviewable and minimal.
- Secrets must never be committed; use environment variables or a secret manager.
- Every user-facing change must be tracked in `CHANGELOG.md` under `Unreleased`.
- The repository root must always contain: `README.md`, `LICENSE`, `.gitignore`, `CHANGELOG.md`, and `CONTRIBUTING.md`.

## 5. Architecture Philosophy

- **Separation of concerns:** the business layer and the AI OS remain independent codebases with clearly defined boundaries.
- **Content-first, SEO-native:** every page is built with SEO, performance, and crawlability in mind.
- **Data-driven:** content, product, and traffic decisions follow analytics, not guesswork.
- **Boring technology:** prefer simple, well-supported, mainstream tools over clever or novel stacks.
- **Automation with boundaries:** automate business workflows, never AI OS capabilities.
- **Privacy and security first:** minimal data collection, secure defaults, and full affiliate disclosure compliance.

## 6. Relationship with Universal AI Content Operating System

- The **AI OS** is the content intelligence and automation engine. It **already exists** in its own repository.
- This repository is the **website/business layer** and never reimplements AI OS functionality.
- The two systems interact **only through documented, versioned interfaces** (e.g., APIs) defined in future integration documentation.
- No code is shared between repositories, and no module is copied in either direction.
- Integration changes are coordinated, reviewed, and documented before they land.

## 7. "No Duplicate Features" Policy

- **The AI OS already exists. Do not build, copy, or adapt any part of it here.**
- Any feature request or pull request that duplicates an existing AI OS capability will be **rejected** during review.
- When a feature seems to overlap with the AI OS, stop and ask: *"Does the AI OS already do this?"* If the answer is yes, integrate through its interface instead of reimplementing.
- This policy applies to code, architecture, and documentation.

## 8. Development Rules

- **Docs before code:** no implementation until scope, architecture, and data model docs are approved.
- **Separate concerns:** website changes belong here; AI OS changes belong in the AI OS repository.
- **Small, reviewable changes:** prefer focused commits and pull requests.
- **Conventional commits:** use `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, and `test:` prefixes.
- **Testing:** automated tests are required once implementation begins.
- **No secrets:** env files, keys, and tokens must never be committed.
- **Quality gates:** linting, formatting, and tests must pass before merging.
- **License compliance:** only MIT-compatible dependencies may be introduced.

## 9. Future Roadmap

- **Phase 0 — Foundation (current):** repository, documentation, and governance in place.
- **Phase 1 — Website foundation:** tech stack decision, design system, deployment pipeline, analytics scaffold.
- **Phase 2 — Articles:** publishing workflow, article templates, and SEO fundamentals.
- **Phase 3 — Affiliate products:** product catalog, affiliate links, disclosures, and revenue tracking.
- **Phase 4 — Pinterest:** pin automation, board management, and traffic attribution.
- **Phase 5 — SEO and traffic:** sitemaps, structured data, performance budgets, and growth experiments.
- **Phase 6 — Analytics and revenue:** dashboards, reporting, and optimization loops.
- **Phase 7 — Automation:** business workflow automation (notifications, reporting, publishing pipelines).
- **Phase 8 — Admin dashboard:** operations dashboard for content, products, and metrics.
- **Ongoing — AI OS integration:** connect to the AI OS through documented APIs only.

---

## Architecture

The complete website architecture (business layer only) is maintained in [docs/architecture](docs/architecture/README.md). It covers system layers, module boundaries, data flow, API flow, responsibilities, security boundaries, and deployment strategy — with the Universal AI Content Operating System treated strictly as an external system accessed only through the AI OS Bridge. The binding boundary rule is the [Website Architecture Contract](docs/architecture/09-website-architecture-contract.md), which must be ratified before any implementation begins. The permanent project folder blueprint is [01-folder-structure.md](docs/architecture/01-folder-structure.md). The permanent, frozen technology stack is [10-technology-stack.md](docs/architecture/10-technology-stack.md). The permanent production database blueprint is [11-database-architecture.md](docs/architecture/11-database-architecture.md). The frozen API contracts are [12-api-contracts.md](docs/architecture/12-api-contracts.md) and the permanent UI/UX design system is [13-ui-ux-design-system.md](docs/architecture/13-ui-ux-design-system.md). The master implementation roadmap is [14-implementation-roadmap.md](docs/architecture/14-implementation-roadmap.md).

---

## Development

Prerequisites: Python 3.11+, Node.js 20+, Docker, Docker Compose.

Backend / API gateway (M1):

```bash
make setup        # create .venv and install foundation dependencies
make check        # lint, format check, typecheck, no-AI guard, tests
make docker-up    # build and start api, postgres, redis (compose)
make health       # GET /health
```

Frontend (M2 — web + admin wireframes on the shared design system):

```bash
npm ci            # install workspace dependencies (lockfile committed)
npm run dev:web   # public website  -> http://localhost:3000
npm run dev:admin # admin dashboard -> http://localhost:3001
npm run lint      # eslint (all workspaces)
npm run typecheck # tsc --noEmit (all workspaces)
npm test          # vitest + axe a11y tests (all workspaces)
npm run build     # next build (web + admin)
```

The implementation roadmap is [14-implementation-roadmap.md](docs/architecture/14-implementation-roadmap.md); M1 (foundation) and M2 (frontend foundation) are complete, M3 (backend + database) is next.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening issues or pull requests.
