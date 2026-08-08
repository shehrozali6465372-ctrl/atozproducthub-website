# ADR-0003 — Shared Backend Core Library

- **Status:** Accepted
- **Date:** 2026-08-07
- **Owner:** @atoz/platform, @atoz/lead
- **Documents affected:** 01-folder-structure.md, 10-technology-stack.md, 14-implementation-roadmap.md

## Context

Phase 3 (Backend Foundation) requires every backend component to share the
same production infrastructure: configuration, structured logging, request
middleware (request ID, CORS, compression, rate limiting, security headers),
database connections (PostgreSQL/Redis), migration plumbing, repository/unit
of work patterns, an event system, background worker scaffolding (Celery),
authentication primitives (JWT, RBAC, sessions, password hashing, MFA
placeholders), secrets loading, and observability hooks.

The Folder Blueprint (§6.3) allows services to import only their own package,
`libs/contracts/`, and `libs/domain-core/`. Duplicating this foundation in
eight services would violate the blueprint's one-way dependency and
maintenance rules; the blueprint (§6.4) requires an ADR for any new shared
library.

## Decision

Create `libs/backend-core` (package `atoz-backend-core`, module
`atoz_backend_core`):

- **Contents:** framework and infrastructure primitives only — no business
  logic, no domain entities, no AI behavior. All modules are opt-in and
  importable independently.
- **Dependency direction:** `atoz_backend_core` depends only on its own
  third-party dependencies (FastAPI, SQLAlchemy, Redis, Celery, PyJWT,
  pwdlib, prometheus-client, jsonschema). It never imports apps, services,
  contracts, or the AI OS.
- **Consumption:** `apps/api` and every `services/*` declare
  `atoz-backend-core` as a dependency; editable install order is
  backend-core first, then consumers.
- **Boundaries:** the library never touches business data, never calls the AI
  OS, and never implements business rules. Domain behavior remains in
  services; contracts remain in `libs/contracts/`.
- **Future:** Phase 4+ adds per-service models/migrations on top of the
  shared `Base` and session factories; any new shared library still requires
  its own ADR.

## Consequences

- One implementation of logging, middleware, auth primitives, events,
  repositories, workers, and observability across the gateway and services.
- CI installs backend-core before installing any service (editable, in
  dependency order).
- The gateway keeps its existing M1 modules; its logging module becomes a
  thin re-export of the shared implementation to avoid duplication.

## Contract compliance

- No AI duplication: the library contains no generation, learning, memory,
  prompt, routing, or model code; CI no-AI guard scans it like every tree.
- Business layer only: all intelligence remains in the AI OS and enters the
  website only through the AI OS Bridge.
