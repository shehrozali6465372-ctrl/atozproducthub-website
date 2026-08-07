# @atoz/web — Public website

Next.js App Router application for the AtozProductHub business front door.

**M2 scope (foundation):** design-system-driven wireframes for every public
page defined in UI/UX Design System §11.2. All content is static mock data;
no business features (articles CMS, affiliate, Pinterest, SEO service,
analytics) are implemented yet.

- Routing: `src/app/**` (App Router)
- Design tokens/components: `@atoz/design-system` (workspace)
- Data: `src/lib/api-client.ts` — typed client stub backed by `src/lib/mock-data.ts`.
  Replaced in Phase 6 by a contract-generated client over `libs/contracts`.
- Tests: `tests/` (vitest + @testing-library/react + axe-core)

## Commands

```bash
npm run dev        # http://localhost:3000
npm run lint       # eslint
npm run typecheck  # tsc --noEmit
npm test           # vitest
npm run build      # next build
```
