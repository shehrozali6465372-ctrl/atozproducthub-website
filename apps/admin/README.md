# @atoz/admin — Admin dashboard

Next.js App Router application for the AtozProductHub operator surface.

**M2 scope (foundation):** wireframes for the seven admin pages defined in
UI/UX Design System §11.2 (login, dashboard, analytics, revenue, pinterest,
automation, settings). All data is static mock data; auth, RBAC, and
read-model integration arrive in Phases 5 and 11.

- Routing: `src/app/**` — `(app)` route group holds the sidebar/topbar shell.
- Design tokens/components: `@atoz/design-system` (workspace)
- Data: `src/lib/api-client.ts` — typed client stub backed by `src/lib/mock-data.ts`.
- All admin pages are `noindex` (Design System §14).
- Tests: `tests/` (vitest + @testing-library/react + axe-core)

## Commands

```bash
npm run dev        # http://localhost:3001
npm run lint
npm run typecheck
npm test
npm run build
```
