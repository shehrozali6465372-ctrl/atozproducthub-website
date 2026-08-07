# @atoz/design-system

Shared UI/UX design system for AtozProductHub (ADR-0001). One design language
across the public site and the admin suite (UI/UX Design System §1.6).

## Boundaries

- **Presentation only.** Tokens, layout, and core components. No business
  logic, no data fetching, no API calls, no AI behavior (Design System §16).
- **Consumed by apps only.** `apps/web` and `apps/admin` import via the
  workspace name; the library never imports apps, services, or contracts.
- **Frozen design rules.** Tokens mirror `docs/architecture/13-ui-ux-design-system.md`
  §3–§8 exactly; component changes require design review (13 §9.8, §17).

## Contents

| Area | Location | Notes |
|------|----------|-------|
| Tokens (color, type, spacing, breakpoints) | `src/styles/tokens.css` | Tailwind v4 `@theme`, light/dark runtime vars |
| Theme (light/dark/system) | `src/theme/` | `ThemeProvider`, pre-paint `ThemeScript`, `ThemeToggle` |
| Layout | `src/components/layout/` | Header, footer, hero, prose, admin shell, breadcrumbs |
| Primitives | `src/components/primitives/` | Button, Badge, Card |
| Forms | `src/components/forms/` | Field, Input, Textarea, Select, Checkbox, Switch, Search, Filters |
| Navigation | `src/components/navigation/` | Breadcrumbs, Pagination |
| Feedback | `src/components/feedback/` | Notifications, Toasts, EmptyState, DisclosureBadge |
| Data display | `src/components/data-display/` | Table (responsive), KPI cards, ContentCard, Avatar |
| Charts | `src/components/charts/` | Recharts wrappers + accessible data-table fallbacks |

## Usage

```css
/* app globals.css */
@import "@atoz/design-system/styles.css";
```

```tsx
import { ThemeProvider, Button, Card } from "@atoz/design-system";
```

Both Next.js apps set `transpilePackages: ["@atoz/design-system"]`; the package
exports TypeScript source directly (no build step).

## Testing

`npm run test` — vitest + @testing-library/react + axe-core (WCAG checks) in
jsdom. Lint: `npm run lint` (typescript-eslint). Types: `npm run typecheck`.
