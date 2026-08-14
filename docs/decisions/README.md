# Architecture Decision Records (ADRs)

ADRs record architecturally significant decisions and the approved changes to
frozen planning documents (Folder Blueprint, Technology Stack, Database
Blueprint, API Contracts, UI/UX Design System, Implementation Roadmap).

## Process

1. **Propose** — create `docs/decisions/NNNN-title.md` using the template below.
2. **Review** — Lead Software Architect + affected module owners; every ADR must
   confirm compliance with the Website Architecture Contract (no AI duplication,
   business-layer-only, Bridge-only AI OS access).
3. **Approve** — decisions changing a frozen document also require a
   `CHANGELOG.md` entry and (for contracts) registry update.
4. **Record** — the ADR stays permanent; superseded ADRs are marked
   `Status: Superseded by NNNN`.

## Index

- ADR-0001 — Shared design system (`libs/design-system`)
- ADR-0002 — Automation service owns the automation database (`automation_db`)
- ADR-0003 — Backend-core library (`libs/backend-core`)
- ADR-0004 — Content service owns the CMS database (`content_db`)
- ADR-0005 — Affiliate service owns the affiliate database (`affiliate_db`)
- ADR-0006 — Pinterest service owns the Pinterest database (`pinterest_db`)
- ADR-0007 — SEO service owns the SEO & discovery layer (`seo_db`)
- ADR-0008 — Analytics service owns the analytics database (`analytics_db`)
- ADR-0009 — Admin service owns the admin & operations control plane (`admin_db`)
- ADR-0010 — Automation service owns the automation database (`automation_db`); Platform queue/job tables stay admin-owned
- ADR-0011 — Executor framework, service-to-service JWT, and single-scheduler Beat

## Template

```markdown
# ADR-NNNN — Title

- **Status:** Proposed | Accepted | Superseded
- **Date:** YYYY-MM-DD
- **Owner:** @atoz/...
- **Documents affected:** 01-folder-structure.md, ...

## Context

## Decision

## Consequences

## Contract compliance
```
