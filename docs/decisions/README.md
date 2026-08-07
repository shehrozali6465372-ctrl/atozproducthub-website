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
