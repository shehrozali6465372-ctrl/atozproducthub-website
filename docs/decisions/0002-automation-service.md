# ADR-0002 — Automation Service Skeleton

- **Status:** Accepted
- **Date:** 2026-08-07
- **Owner:** @atoz/lead, @atoz/platform
- **Documents affected:** 01-folder-structure.md, 03-module-boundaries.md, 14-implementation-roadmap.md

## Context

The Implementation Roadmap Phase 12 (Automation) and the Folder Blueprint
place business automation in `pipelines/jobs/` and `services/*/workflows/`.
Task 13 (M3 Backend Foundation) mandates a dedicated `automation-service`
skeleton alongside the seven blueprint services so every future business
module has a home from day one.

The Folder Blueprint (§1, §6.4) requires an ADR before adding folders or
shared libraries.

## Decision

Create `services/automation-service/` as a standard service skeleton:

- **Responsibility (future):** business automation workflows — scheduling,
  running, and auditing business automations (pin queue replenishment,
  affiliate reconciliation, sitemap refresh, report generation).
- **Boundary:** business workflows only. AI OS automation (content
  generation, insights scheduling on the AI OS side) stays in the AI OS;
  the website requests AI OS work only through the AI OS Bridge.
- **Relationship to `pipelines/jobs/`:** `pipelines/jobs/` remains the home
  of deployment-time and operational CI/CD automations; `automation-service`
  hosts long-running business workflow execution, scheduled rules, and run
  history read models.

## Consequences

- `services/` now has eight skeletons (seven blueprint + automation).
- All other blueprint conventions apply unchanged (per-service package,
  per-service db/migrations, no cross-service imports, contracts via
  `libs/contracts/`).

## Contract compliance

- No AI functionality: the service hosts business workflow execution only;
  nothing here generates, learns, researches, or routes intelligence.
- Business layer only; AI OS contact remains exclusively via the Bridge.
