# ADR-0001 — Shared Design System Workspace

- **Status:** Accepted
- **Date:** 2026-08-07
- **Owner:** @atoz/web, @atoz/admin, @atoz/lead
- **Documents affected:** 01-folder-structure.md, 10-technology-stack.md, 13-ui-ux-design-system.md, 14-implementation-roadmap.md

## Context

The UI/UX Design System (13) requires **one design language across the public
site, landing pages, and the admin suite** (13 §1.6). The Implementation
Roadmap Phase 2 scaffolds `apps/web` and `apps/admin` in the same milestone
with the complete visual foundation (tokens, theme, layout, core components).

The Folder Blueprint (01) currently defines `libs/` as contracts-only
(`libs/contracts/`, `libs/domain-core/`). Without a shared home for design
tokens and UI primitives, the two apps would either duplicate the design
system or depend on each other — both violate the blueprint's one-way
dependency rules (01 §6.3, §6.4).

## Decision

Create a new shared workspace `libs/design-system` (package `@atoz/design-system`):

- **Contents:** design tokens (CSS custom properties + Tailwind v4 `@theme`
  mapping per 13 §3–§8), theme provider (light/dark, `prefers-color-scheme`,
  persisted), layout primitives (header, footer, nav, sidebar, breadcrumbs,
  container, skip link), and core components (button, badge, card, form
  fields, table, notifications, search, pagination, filters, charts, KPI
  cards, disclosure badge).
- **Ownership:** `@atoz/lead` + design review; new components require design
  review per 13 §9.8.
- **Dependency direction:** `libs/design-system` imports only React, Radix
  primitives, Lucide, and Recharts (frozen stack 10 §2). It never imports
  apps, services, or contracts. Apps import it via the workspace name only.
- **Boundaries:** the library contains presentation only — no business logic,
  no data fetching beyond inert mock props, no API calls, no AI behavior
  (13 §9.7, §16).
- **Future:** the mobile app (Phase 13+) reuses the same tokens and primitives
  per 13 §17 and roadmap Phase 2 future integrations.

## Consequences

- `libs/` gains a second, design-scoped namespace. Contract schemas remain in
  `libs/contracts/`; no contract behavior moves here.
- Both Next.js apps declare `transpilePackages: ["@atoz/design-system"]` and
  consume TypeScript source directly (no build step, single source of truth).
- CI gains a frontend job (lint, typecheck, build, vitest + axe) that covers
  the library and both apps.
- Any new shared library beyond contracts and the design system still
  requires its own ADR (01 §6.4).

## Contract compliance

- **No AI duplication:** the library contains no generation, learning,
  research, memory, prompt, routing, or model code; CI no-AI guard scans it
  like every other tree.
- **Business layer only:** the library renders business data; all intelligence
  remains in the AI OS and reaches the website only through the AI OS Bridge.
- **One-way dependencies preserved:** apps → design-system → (React/Radix/
  Lucide/Recharts); the design system never depends on apps or services.
