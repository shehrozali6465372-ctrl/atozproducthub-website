# 13 — UI/UX Design System (Permanent UI/UX Blueprint)

**Status:** Permanent design system — binding for all future implementation
**Version:** 1.0
**Compliance:** Must satisfy the [Website Architecture Contract](09-website-architecture-contract.md), the [Technology Stack](10-technology-stack.md), and the [API Contracts](12-api-contracts.md)

This document is the **single source of truth** for the user experience of the AtozProductHub business layer: brand, visual language, components, every page, accessibility, SEO layout, and performance budgets. No code, components, HTML, or CSS are included — design documentation only.

---

## 1. Design Philosophy

1. **Content first, commerce gently.** Articles are the hero; affiliate products appear as helpful, clearly disclosed recommendations — never intrusive.
2. **Trust by design.** Fast pages, clear disclosure, transparent data, honest voice. Every monetized surface visibly says why it earns a commission.
3. **Readers move fast; designers stay out of the way.** Scannable layouts, strong hierarchy, minimal clutter, 3-click depth.
4. **Business layer only.** The UI displays business information and AI OS *outputs* (approved articles, pin assets, insights). The UI contains no AI functionality — no chat, no prompt inputs, no generation tools, no "AI" branding beyond attribution of AI OS-provided insights.
5. **Consistent, boring, reliable.** One design language across the public site, landing pages, and the admin suite. Novelty is a review blocker.
6. **Accessible and fast are features.** WCAG 2.1 AA and Core Web Vitals budgets are design constraints, not afterthoughts.
7. **Mobile first, CDN ready.** Every layout is designed small-screen-first and cache-friendly.

## 2. Brand Identity

- **Brand essence:** "A helpful friend who already did the research."
- **Positioning:** AtozProductHub is a trusted product-discovery and content hub — articles that teach, recommendations that are tested, disclosures that are always visible.
- **Brand values:** Clarity, Honesty, Utility, Craft, Growth.
- **Voice:** plain, knowledgeable, friendly, no hype, no fear. Speaks to the reader as a smart friend.
- **Tone by context:** articles = instructive; product pages = factual + persuasive-light; admin = neutral operational; legal = plain and precise.
- **Tagline:** "Products worth knowing." (placeholders are design guidance, final copy owned by content/brand)
- **Logo guidance (not a design):** wordmark "AtozProductHub" with a discovery mark (open compass/loop motif); minimum clear-space = height of the "A"; monochrome versions for light/dark; favicon = mark only.
- **Messaging rules:** never claim AI authorship on the website; AI OS-provided content is presented as AtozProductHub content; AI OS insights in dashboards carry an "AI OS insights" attribution label.

## 3. Color System

Token naming: `--color-<role>-<step>` (implemented later as CSS variables). Palette is designed for WCAG 2.1 AA contrast.

| Token | Light value | Dark value | Usage |
|-------|-------------|------------|-------|
| `--color-primary-500` | #4F46E5 (indigo) | #818CF8 | Primary actions, links, active states |
| `--color-primary-600` | #4338CA | #6366F1 | Hover/emphasis (AA on light bg) |
| `--color-accent-500` | #D97706 (amber) | #F59E0B | Affiliate/commission highlights, badges |
| `--color-success-500` | #059669 | #34D399 | Success, revenue positive |
| `--color-warning-500` | #D97706 | #FBBF24 | Warnings, pending states |
| `--color-danger-500` | #DC2626 | #F87171 | Errors, destructive actions |
| `--color-info-500` | #0284C7 | #38BDF8 | Information, AI OS insights label |
| `--color-surface-0` | #FFFFFF | #0B1220 | Page background |
| `--color-surface-1` | #F8FAFC | #111A2E | Card/raised background |
| `--color-surface-2` | #F1F5F9 | #1A2540 | Hovered/input background |
| `--color-border` | #E2E8F0 | #2A3754 | Dividers, borders |
| `--color-text-900` | #0F172A | #F1F5F9 | Primary text |
| `--color-text-600` | #475569 | #94A3B8 | Secondary text |
| `--color-text-400` | #94A3B8 | #64748B | Muted/label text |

**Rules:** primary ≤ 2 roles per screen; accent reserved for affiliate/commission signals; destructive actions always danger; text never uses pure black/white; all interactive text ≥ 4.5:1 contrast, large text ≥ 3:1; status is never color-only (always paired with icon/text).

## 4. Typography

| Role | Family | Weights | Notes |
|------|--------|---------|-------|
| UI (headers, nav, buttons, admin) | Inter (sans) | 400/500/600/700 | Variable font, system fallbacks |
| Article body (long-form) | Lora (serif) | 400/500/600 | Readability for 8+ minute reads |
| Data/statistics (dashboards) | JetBrains Mono (mono) | 400/600 | Numbers align tabularly |

**Fluid type scale** (mobile → desktop, `clamp()` in implementation):

| Step | Size mobile | Size desktop | Role |
|------|-------------|--------------|------|
| display | 32–40 px | 48–56 px | Home hero, page titles |
| h1 | 28 px | 40 px | Article/page title |
| h2 | 22 px | 30 px | Section titles |
| h3 | 18 px | 22 px | Card/subsection titles |
| body-lg | 17 px | 19 px | Article body (Lora) |
| body | 16 px | 16 px | Default |
| small | 14 px | 14 px | Meta, captions |
| label | 12–13 px | 13 px | Labels, badges, table headers |

**Rules:** line-height 1.4 (UI) / 1.7 (article body); max measure 72–78 chars for body; heading hierarchy is semantic (one h1 per page); no all-caps beyond labels; numerals in mono on dashboards only.

## 5. Icons

- **Set:** Lucide (frozen in Technology Stack), stroke 1.75 px, rounded caps/joins.
- **Sizes:** 16 (inline/labels), 20 (buttons), 24 (empty states/nav), 32 (feature icons).
- **Rules:** icons support, never replace, text labels; status icons always paired with color + text; decorative icons are `aria-hidden`; icons are keyboard-focusable only when interactive.
- **Affiliate/commission icon:** the accent-colored badge icon is reserved for monetized content and always accompanies the disclosure label.

## 6. Layout System

**Page archetypes:**

| Archetype | Pages | Layout shape |
|-----------|-------|--------------|
| Marketing | Home, About, Contact | Hero → sections → CTA |
| Content | Article, Category, Tag, Search results | Header → article/rail or list |
| Storefront | Product, Affiliate Collection | Gallery + details / curated grid |
| Landing | Pinterest Landing Page | Pin-consistent hero → list → CTA |
| Utility | Privacy, Terms, Disclaimer, Sitemap, 404 | Narrow prose column |
| Admin | Login, Dashboard, Analytics, Revenue, Pinterest, Automation, Settings | App shell: sidebar + topbar + workspace |

**App shell regions:** site header (public) / admin topbar (admin), primary navigation, main content, optional sidebar/rail, footer (public only). Container max-width 1200 px, article content column 680–720 px.

**Rules:** one primary action per view; every page has a clear h1; content never scrolls horizontally; sticky headers ≤ 64 px mobile / 72 px desktop; breadcrumbs on all non-home, non-admin pages.

## 7. Grid System

- **Base:** 12-column grid; gutters 16 px (mobile) / 24 px (tablet) / 32 px (desktop); max container 1200 px.
- **Content page:** single 12-col column at ≤ 1024 px; article column (8) + rail (4) at ≥ 1024 px.
- **Storefront:** 2-col (mobile) → 3-col (tablet) → 4-col (desktop) product cards.
- **Admin:** sidebar (3) + workspace (9); dashboards use 12-col with card spans 3/4/6/12.
- **Rules:** no fixed-pixel widths; grids collapse to single column under 768 px; card grids degrade to stacked lists on very small screens.

## 8. Spacing System

- **Base unit:** 4 px. Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96 (tokens `--space-1..--space-9`).
- **Defaults:** section padding 48/64 (mobile/desktop); card padding 16/24; list gaps 12/16; grid gutters 16/24/32.
- **Rules:** spacing only from the scale; internal component padding ≥ 8 px; tap targets ≥ 44 × 44 px; article paragraphs spaced 24 px, headings 32 px before / 16 px after.

## 9. Component Design Rules

Universal standards every component must follow:

1. **Anatomy first:** every component defines container, content, and optional adornments; no decoration without purpose.
2. **State coverage:** default, hover, active, focus-visible, disabled, error (forms), loading, empty. Missing states = review blocker.
3. **Focus:** visible 2 px focus ring (`--color-primary-500`), never removed.
4. **Semantics:** use native elements/roles; interactive components are keyboard-operable.
5. **Responsive:** every component has a mobile, tablet, and desktop treatment.
6. **Performance:** no component may block first paint; images lazy-load below the fold with explicit dimensions.
7. **No AI behavior:** no component calls AI, generates content, or renders prompts. AI OS-provided content renders as normal business content; AI OS insights render in read-only "insight" cards with attribution.
8. **Ownership:** components are defined in the design system before implementation; new components require design review.

## 10. Responsive Design Rules

- **Breakpoints:** mobile-first — base 320+ · sm 640 · md 768 · lg 1024 · xl 1280 · 2xl 1440.
- **Behavior model:**
  - Navigation: horizontal bar ≥ lg; hamburger/drawer < lg.
  - Tables (admin): keep horizontal ≥ md; transform to card lists < md.
  - Filters: inline ≥ lg; collapsible drawer < lg.
  - Charts: full-width ≥ md; simplified single-metric cards < md.
  - Cards: grid columns scale per Section 7.
- **Text:** fluid type (Section 4); no horizontal scroll; images scale with containers.
- **Touch:** targets ≥ 44 px on all breakpoints; hover effects never required for function.
- **Rule:** every page is designed, reviewed, and tested at 360, 768, 1024, and 1440 px.

---

## 11. Page Design System

Every page is specified with the same template: **Purpose, User Journey, Main Components, SEO Importance, Pinterest Importance, Affiliate Importance, Analytics Events.**

### 11.1 Wireframes (core archetypes)

```
HOME (desktop)
┌──────────────────────────────────────────────┐
│ Logo   Nav[Home Articles Products About]  🔍 │  header
├──────────────────────────────────────────────┤
│ Hero: "Products worth knowing."  [CTA: Explore]│
├──────────────────────────────────────────────┤
│ Popular Articles  [card][card][card]         │
│ Featured Collections [card][card][card]      │
│ Latest from Pinterest [pin][pin][pin][pin]   │
│ Newsletter strip                    [Sign up] │
├──────────────────────────────────────────────┤
│ Footer: links, disclosure, legal             │
└──────────────────────────────────────────────┘
```

```
ARTICLE (desktop)
┌──────────────────────────────────────────────┐
│ Logo  Nav            Breadcrumbs: Home > Cat  │
├──────────────────────┬───────────────────────┤
│ H1 Article title      │ Rail:                  │
│ Meta (date, author,   │  Table of contents    │
│   read time)          │  Related articles     │
│ Featured image        │  [Affiliate card]     │
│ Body (Lora serif)     │  [Affiliate card]     │
│ In-article product    │  Disclosure badge     │
│   card w/ disclosure  │                       │
│ Related articles      │                       │
└──────────────────────┴───────────────────────┘
```

```
PRODUCT / PINTEREST LANDING (desktop)
┌──────────────────────────────────────────────┐
│ Logo  Nav            Breadcrumbs               │
├──────────────────────┬───────────────────────┤
│ Gallery: [image][…]   │ Title                  │
│                       │ Rating · meta          │
│                       │ Price · [Buy button]   │
│                       │ Disclosure badge       │
│                       │ Pros/cons list         │
│                       │ FAQs (JSON-LD)         │
└──────────────────────┴───────────────────────┘
```

```
SEARCH / CATEGORY (desktop)
┌──────────────────────────────────────────────┐
│ Logo  Nav          [Search box]  [Filters ▾]  │
├───────────┬──────────────────────────────────┤
│ Filters   │ Results list/grid (cards)         │
│ (sidebar) │ [card][card][card][card]          │
│ Niche     │ Pagination                        │
│ Category  │                                  │
└───────────┴──────────────────────────────────┘
```

```
ADMIN DASHBOARD (desktop)
┌──────────┬───────────────────────────────────┐
│ Sidebar  │ Topbar: search, notifications, 🧑 │
│ Overview │ ┌───────────────────────────────┐ │
│ Content  │ │ KPI cards: traffic, revenue,  │ │
│ Pinterest│ │  pins, SEO health              │ │
│ Affiliate│ └───────────────────────────────┘ │
│ SEO      │ [Revenue chart] [Traffic chart]   │
│ Analytics│ [Pin status table] [SEO health]   │
│ Automation│ [AI OS insights card (read-only)] │
│ Settings │                                   │
└──────────┴───────────────────────────────────┘
```

### 11.2 Page specifications

#### Public pages

**1. Home**
- **Purpose:** The business front door: communicate the brand, route readers to content, products, and pin-driven entry points; build trust.
- **User Journey:** Land → scan value proposition → choose a path (popular article, collection, pin gallery) → click through; returners find fresh content quickly.
- **Main Components:** Header/nav, hero, article cards, collection cards, Pinterest pin gallery, newsletter strip, footer.
- **SEO Importance:** Highest — homepage metadata, brand search presence, internal linking hub, fresh-content signals.
- **Pinterest Importance:** Pin gallery surfaces the Pinterest channel and reinforces pin→site loops.
- **Affiliate Importance:** Featured collections are the affiliate entry points; disclosure strip visible.
- **Analytics Events:** `page_view`, `home.hero_click`, `home.card_click`, `newsletter.signup`.

**2. Article**
- **Purpose:** Serve the core content product: teach, rank, and naturally recommend affiliate products.
- **User Journey:** Search/pin/social → article → read → explore in-article product cards → related article or product page.
- **Main Components:** Breadcrumbs, h1, meta, featured image, TOC rail, article body, in-article affiliate cards with disclosure, related articles, footer.
- **SEO Importance:** Primary ranking asset — metadata, JSON-LD (`Article`), headings, internal links, readability, CWV.
- **Pinterest Importance:** Article is the destination of pins; pin-save buttons; pin-attributed visits land here.
- **Affiliate Importance:** In-article product recommendations with visible disclosure convert readers.
- **Analytics Events:** `page_view`, `article.read_depth`, `affiliate_click`, `article.related_click`, `pin_save`.

**3. Category**
- **Purpose:** Organize articles by niche topic; a hub for crawlers and readers exploring a subject.
- **User Journey:** Navigate/search → category hub → browse article list → article or subcategory.
- **Main Components:** Breadcrumbs, category description, article grid/list, subcategory links, pagination, rail.
- **SEO Importance:** High — hub pages collect internal links and topical authority; JSON-LD (`CollectionPage`).
- **Pinterest Importance:** Category-level pins land here; pin gallery for the category.
- **Affiliate Importance:** Category pages may feature a curated collection card.
- **Analytics Events:** `page_view`, `category.filter`, `article_click`, `pagination`.

**4. Tag**
- **Purpose:** Group cross-cutting topics (e.g., "budget," "wireless") for discovery and long-tail SEO.
- **User Journey:** Click tag → list of tagged articles → article.
- **Main Components:** Breadcrumbs, tag title, article list, related tags, pagination.
- **SEO Importance:** Long-tail indexable pages; thin-content guard (index only when ≥ N articles).
- **Pinterest Importance:** Low; tags may feed pin descriptions.
- **Affiliate Importance:** None direct.
- **Analytics Events:** `page_view`, `tag_click`, `article_click`.

**5. Search**
- **Purpose:** Let readers find articles and products by intent.
- **User Journey:** Type query → results (articles + products) → refine filters → click result.
- **Main Components:** Search box, filter sidebar (niche, type, sort), result cards, pagination, empty state with suggestions.
- **SEO Importance:** Medium — search results pages generally `noindex`; site search feeds Typesense.
- **Pinterest Importance:** None direct.
- **Affiliate Importance:** Product results are affiliate entry points with disclosure.
- **Analytics Events:** `search.query`, `search.result_click`, `search.filter`, `search.no_results`.

**6. Product**
- **Purpose:** Recommend and sell an affiliate product with full transparency.
- **User Journey:** Pin/search/article → product page → read details → click buy (disclosed) → affiliate network → back or related.
- **Main Components:** Breadcrumbs, gallery, title/rating/meta, price, buy button, disclosure badge, pros/cons, specs, FAQs, related products.
- **SEO Importance:** High — product JSON-LD (`Product`), review/FAQ schema, ranking for product queries.
- **Pinterest Importance:** Product pages are pin destinations; pin saves from gallery.
- **Affiliate Importance:** The monetization core — buy CTA, click attribution, disclosure compliance.
- **Analytics Events:** `page_view`, `affiliate_click`, `product.gallery`, `product.faq_open`, `pin_save`.

**7. Pinterest Landing Page**
- **Purpose:** Convert Pinterest traffic into a focused reader path per niche/account.
- **User Journey:** Pin click → landing page matching pin promise → article/product list → engagement or save.
- **Main Components:** Pin-consistent hero (title/image matching the pin), content list, related pins, CTA, disclosure.
- **SEO Importance:** Medium — these pages are indexable entry points; metadata mirrors the pin title (consistency improves CTR).
- **Pinterest Importance:** Highest — the destination of pins; per-account, per-niche landing variants; attribution (`pinterest_account_id`).
- **Affiliate Importance:** Lists lead to product pages; disclosure visible.
- **Analytics Events:** `page_view`, `landing.pin_attributed`, `article_click`, `affiliate_click`, `pin_save`.

**8. Affiliate Collection**
- **Purpose:** Curated product roundups ("Best X of 2026") — high-intent affiliate pages.
- **User Journey:** Search/pin/article → collection → compare products → product page or buy.
- **Main Components:** Breadcrumbs, collection intro, product cards (rank, price, pros/cons), buy links with disclosure, FAQs, related collections.
- **SEO Importance:** High — roundup pages rank for buyer-intent keywords; `ItemList`/`Product` JSON-LD.
- **Pinterest Importance:** Collection covers/pins drive traffic; per-pin product cards.
- **Affiliate Importance:** Highest revenue-per-visit page type; strict disclosure.
- **Analytics Events:** `page_view`, `affiliate_click`, `collection.sort`, `collection.compare`.

**9. About**
- **Purpose:** Build brand trust and explain who AtozProductHub is.
- **User Journey:** Footer/social → about → learn mission → trust the site.
- **Main Components:** Hero statement, mission, values, disclosure explanation, team/contact links.
- **SEO Importance:** Low-medium; brand SERP presence, E-E-A-T signal.
- **Pinterest Importance:** None direct.
- **Affiliate Importance:** Transparency strengthens conversion trust.
- **Analytics Events:** `page_view`.

**10. Contact**
- **Purpose:** Provide a human channel (business inquiries, corrections, press).
- **User Journey:** Footer → contact → form → confirmation.
- **Main Components:** Contact form (name, email, reason, message), privacy note, response-time expectation, success state.
- **SEO Importance:** Low; `ContactPage` schema.
- **Pinterest Importance:** None.
- **Affiliate Importance:** Network/merchant inquiries route here.
- **Analytics Events:** `page_view`, `contact.submit`, `contact.error`.

**11. Privacy Policy**
- **Purpose:** Legally required transparency about data, cookies, and consent.
- **User Journey:** Footer/consent banner → read or search policy.
- **Main Components:** Prose layout, TOC, last-updated date, consent/opt-out links.
- **SEO Importance:** Low; `noindex` optional (typically indexed once).
- **Pinterest Importance:** None.
- **Affiliate Importance:** Disclosure of tracking cookies (affiliate + analytics).
- **Analytics Events:** `page_view`, `privacy.optout`.

**12. Terms**
- **Purpose:** Define terms of use for the website.
- **User Journey:** Footer → read terms.
- **Main Components:** Prose, sections, last-updated date.
- **SEO Importance:** Low.
- **Pinterest Importance:** None.
- **Affiliate Importance:** Links/commission terms referenced.
- **Analytics Events:** `page_view`.

**13. Disclaimer**
- **Purpose:** Affiliate and editorial disclaimer — the trust anchor for monetization.
- **User Journey:** Any monetized page link → disclaimer.
- **Main Components:** Prose, affiliate disclosure statement, editorial independence statement, effective date.
- **SEO Importance:** Low.
- **Pinterest Importance:** None direct; pins link to disclosed pages.
- **Affiliate Importance:** Highest compliance relevance — FTC-aligned disclosure.
- **Analytics Events:** `page_view`.

**14. Sitemap**
- **Purpose:** Human-readable index of major sections (HTML sitemap, complements XML sitemaps).
- **User Journey:** Footer → sitemap → choose section.
- **Main Components:** Grouped link lists by niche/category.
- **SEO Importance:** Medium — helps crawlers discover hub pages; typically `noindex`.
- **Pinterest Importance:** None.
- **Affiliate Importance:** None direct.
- **Analytics Events:** `page_view`, `sitemap.link_click`.

**15. 404**
- **Purpose:** Recover lost visitors gracefully.
- **User Journey:** Bad link → 404 → search or popular articles → recovery.
- **Main Components:** Clear message, search box, popular links, report-link option.
- **SEO Importance:** Proper 404 status; helpful recovery reduces bounce.
- **Pinterest Importance:** Dead pins land here — recovery content is important.
- **Affiliate Importance:** None direct.
- **Analytics Events:** `404.view`, `404.search`, `404.recovery_click`.

#### Admin pages

**16. Admin Login**
- **Purpose:** Authenticate operators (OIDC + MFA).
- **User Journey:** Enter email → redirect to IdP → MFA → dashboard.
- **Main Components:** Email field, sign-in button, MFA step, error/session-expired states.
- **SEO Importance:** `noindex`, nofollow — never indexed.
- **Pinterest Importance:** None.
- **Affiliate Importance:** None.
- **Analytics Events:** `admin.login_start`, `admin.login_success`, `admin.login_failed`.

**17. Admin Dashboard**
- **Purpose:** Daily operations overview for the business.
- **User Journey:** Login → KPI overview → drill into any module.
- **Main Components:** Sidebar, topbar, KPI cards, module status summaries, recent activity, AI OS insights card (read-only), audit trail shortcut.
- **SEO Importance:** `noindex`.
- **Pinterest Importance:** Account/pin health summary.
- **Affiliate Importance:** Revenue/click summary.
- **Analytics Events:** `admin.page_view`, `admin.kpi_open`, `admin.module_navigate`.

**18. Analytics Dashboard**
- **Purpose:** Traffic, engagement, and conversion measurement.
- **User Journey:** Dashboard → analytics → filter niche/date/account → inspect charts → export.
- **Main Components:** Date range, niche/account filters, KPI charts (Recharts), funnel, top pages, export button.
- **SEO Importance:** `noindex`.
- **Pinterest Importance:** Pin-attributed traffic breakdown.
- **Affiliate Importance:** Conversion and click-through metrics.
- **Analytics Events:** `admin.page_view`, `analytics.filter`, `analytics.export`.

**19. Revenue Dashboard**
- **Purpose:** Revenue tracking and affiliate performance.
- **User Journey:** Dashboard → revenue → date/network filters → review commissions → reconcile status.
- **Main Components:** Revenue KPI cards, commission chart, network breakdown table, reconciliation status, export.
- **SEO Importance:** `noindex`.
- **Pinterest Importance:** Revenue-by-pin-source view.
- **Affiliate Importance:** Highest financial visibility surface; disclosure settings shortcut.
- **Analytics Events:** `admin.page_view`, `revenue.filter`, `revenue.export`, `revenue.reconcile_run`.

**20. Pinterest Dashboard**
- **Purpose:** Operate 10+ Pinterest accounts: pins, boards, scheduling, health.
- **User Journey:** Dashboard → Pinterest → select account/niche → review queues and health → schedule/manage pins.
- **Main Components:** Account selector, board list, pin queue table, schedule controls, rate-limit/health indicators, failed-pin alerts.
- **SEO Importance:** `noindex`.
- **Pinterest Importance:** Core operational surface — per-account isolation visible in every row/filter.
- **Affiliate Importance:** Pin→click performance feeds product strategy.
- **Analytics Events:** `admin.page_view`, `pinterest.account_switch`, `pin.schedule`, `pin.retry`.

**21. Automation Dashboard**
- **Purpose:** Govern business automations: schedules, runs, failures.
- **User Journey:** Dashboard → automation → review rules and runs → enable/disable → inspect failures.
- **Main Components:** Rules table, run history, status badges, schedule editor, failure queue, audit link.
- **SEO Importance:** `noindex`.
- **Pinterest Importance:** Pin scheduling automations visible here.
- **Affiliate Importance:** Reconciliation/report automations visible here.
- **Analytics Events:** `admin.page_view`, `automation.toggle`, `automation.run_detail`.

**22. Settings**
- **Purpose:** Configure the business layer: niches, accounts, networks, disclosure, roles.
- **User Journey:** Dashboard → settings → choose section → edit → save (audited).
- **Main Components:** Section tabs (niches, Pinterest accounts, affiliate networks, SEO defaults, disclosure, roles/permissions, notifications, API keys), forms, save states.
- **SEO Importance:** `noindex`.
- **Pinterest Importance:** Account binding and token status per niche.
- **Affiliate Importance:** Network credentials/refs and commission defaults.
- **Analytics Events:** `admin.page_view`, `settings.save`, `settings.error`.

---

## 12. Shared UI Components

Every component below follows the Component Design Rules (§9). Spec per component: **Purpose, Anatomy, States, Rules.**

**Navigation (primary)**
- **Purpose:** Route readers/operators to the main areas of the site.
- **Anatomy:** logo, links, search trigger, (admin: workspace switch); mobile drawer.
- **States:** collapsed/expanded, active page, hover, focus, drawer open/closed.
- **Rules:** ≤ 6 public links; active state always visible; drawer is a sibling landmark; admin sidebar follows the same token system.

**Header (public site header)**
- **Purpose:** Brand, primary navigation, search, and trust cues above the fold.
- **Anatomy:** logo lockup, nav, search, optional CTA; sticky ≤ 72 px.
- **States:** scrolled (elevated), focus-visible.
- **Rules:** one logo; never contain promotional clutter; announcement bar (when used) is dismissible and excluded from CLS budget.

**Footer**
- **Purpose:** Navigation fallback, legal/disclosure links, trust and brand close.
- **Anatomy:** brand + tagline, link groups (articles, products, company, legal), disclosure statement, copyright.
- **Rules:** contains links to Privacy, Terms, Disclaimer, Sitemap; disclosure statement always visible; no external scripts.

**Sidebar (admin; optional public rail)**
- **Purpose:** Persistent module navigation (admin) or context rail (public article).
- **Anatomy:** module links with icons, active section, user/role footer (admin); TOC + related cards (public).
- **States:** collapsed (mobile), active, hover, focus.
- **Rules:** admin sidebar icons always paired with labels; public rail collapses below lg.

**Breadcrumbs**
- **Purpose:** Orientation and crawl signals.
- **Anatomy:** `Home > Category > Page` with separators; `aria-label="Breadcrumb"` + `BreadcrumbList` JSON-LD.
- **States:** hover, current-page (non-link).
- **Rules:** on every non-home, non-admin page; never replace the page h1.

**Cards**
- **Purpose:** Group content/product summaries into scannable units.
- **Anatomy:** media (16:9 or 1:1), title, meta, optional CTA, optional disclosure badge; entire card clickable with a single link.
- **States:** hover (elevation), focus-visible, loading (skeleton), empty.
- **Rules:** fixed aspect media (CLS-safe), text truncation limits, one primary action per card.

**Buttons**
- **Purpose:** Trigger actions.
- **Anatomy:** label (+ optional icon), 44 px minimum target; variants: primary, secondary, ghost, danger.
- **States:** default, hover, active, focus-visible, disabled (with reason), loading (spinner).
- **Rules:** one primary button per view; labels are verbs; destructive actions are danger and require confirmation in admin.

**Forms**
- **Purpose:** Collect validated input (contact, settings, admin actions, login).
- **Anatomy:** label, input, hint, error message, submit; grouped with section headings.
- **States:** empty, filled, focus, error, success, disabled, loading-submit.
- **Rules:** labels always visible (no placeholder-only), errors inline + `aria-describedby`, Zod validation mirrors API contracts (12-api-contracts.md §6), sensitive fields autocomplete-correct.

**Tables**
- **Purpose:** Present structured data (admin: pins, jobs, revenue, audit).
- **Anatomy:** header row, sortable columns, row actions, empty state, loading state, optional row selection.
- **States:** hover row, selected, sorted column, loading, empty.
- **Rules:** `<md` transform to card lists; numeric columns mono-aligned; sticky header with pagination; never a table for small lists.

**Charts**
- **Purpose:** Communicate metrics (Recharts): traffic, revenue, pin performance, SEO health.
- **Anatomy:** title, value, series, axes, legend, tooltip, empty/loading states; accessible data table fallback.
- **States:** loading skeleton, hover point, empty, error.
- **Rules:** every chart has a text summary + underlying data table for accessibility; colors from the system palette; no 3D/decoration.

**Notifications**
- **Purpose:** Surface results, errors, approvals, and alerts (toast/in-app).
- **Anatomy:** icon, title, body, action, dismiss; variants: info, success, warning, danger.
- **States:** enter, visible, exiting, stack, unread (admin center).
- **Rules:** auto-dismiss only for non-critical; critical errors require acknowledgment; respect `prefers-reduced-motion`.

**Search**
- **Purpose:** Find articles and products by intent.
- **Anatomy:** input, submit, suggestions dropdown, results page; keyboard-operable.
- **States:** idle, typing, loading, suggestions, no-results, results.
- **Rules:** debounced queries; results are public API data only (no AI), `aria-live` announcements for results.

**Pagination**
- **Purpose:** Navigate long lists (articles, products, admin tables).
- **Anatomy:** prev/next, page numbers (windowed), count, per-page selector (admin).
- **States:** current page, disabled edges, focus.
- **Rules:** windowed pages ≤ 7 numbers; first result follows h1; never paginate inside cards.

**Filters**
- **Purpose:** Narrow lists by niche, category, type, source, date.
- **Anatomy:** filter groups, applied-chip row, clear-all, count; inline ≥ lg, drawer < lg.
- **States:** active/inactive, applied chips, loading, empty result.
- **Rules:** every filter result set is bookmarkable (URL state); filters never mutate data.

**Dark Mode**
- **Purpose:** Reduce glare for readers and operators; accessibility feature.
- **Anatomy:** theme toggle (public footer/header; admin topbar), `prefers-color-scheme` default, persisted choice.
- **Rules:** token-driven (Section 3), full contrast parity with light mode, images unaffected, toggle never causes layout shift.

---

## 13. Accessibility

- **Standard:** WCAG 2.1 AA across all pages and components.
- **Structure:** semantic landmarks (`header`, `nav`, `main`, `aside`, `footer`), skip-to-content link, one `h1` per page, logical heading order.
- **Keyboard:** every interaction keyboard-operable; visible focus ring; no focus traps (except modal/drawer with managed focus).
- **Forms:** visible labels, inline errors with `aria-describedby`, required indicators not color-only.
- **Images:** descriptive alt text; decorative images `alt=""` + `aria-hidden`; no text in images.
- **Contrast:** text ≥ 4.5:1; large text ≥ 3:1; focus indicators ≥ 3:1 against adjacent.
- **Motion:** `prefers-reduced-motion` — disable animations, smooth scroll, and auto-dismissals.
- **Assistive tech:** tables use real table semantics; charts have data-table fallbacks; notifications use `role="status"`/`role="alert"` appropriately.
- **Testing gates:** automated axe checks in CI + keyboard walkthrough per release; design review blocks releases with a11y regressions.

## 14. SEO Layout and Core Web Vitals

**SEO layout rules**
- Metadata (title, description, canonical, robots, OG/Twitter) rendered server-side on every page (Next.js metadata API).
- JSON-LD by page type: `Article`, `Product`, `CollectionPage`, `BreadcrumbList`, `FAQPage`, `Organization`, `ContactPage`.
- Semantic HTML and heading order align with content hierarchy; article measure 72–78 chars.
- Internal linking: category hubs, related articles, breadcrumbs; URL policy owned by `seo-service`.
- Sitemaps: HTML sitemap page + XML shards served from CDN; `noindex` for search, filters, admin, pagination beyond policy.
- Affiliate links: disclosure-adjacent, `rel="sponsored nofollow"` on outbound affiliate links, internal paths crawlable.

**Core Web Vitals budgets**

| Metric | Budget | Design contribution |
|--------|--------|---------------------|
| LCP | ≤ 2.5 s | Server-rendered hero, preloaded LCP image, no layout shifts |
| INP | ≤ 200 ms | Minimal client JS, no long tasks, virtualized long lists |
| CLS | ≤ 0.1 | Reserved media dimensions, stable fonts (`font-display`), no injected banners |
| TTFB | ≤ 800 ms | CDN/edge delivery, cache-first |

**Rules:** images lazy-load below the fold with explicit width/height; fonts subsetted; third-party scripts (Pinterest Tag, analytics) loaded async after interaction where possible; every release runs Lighthouse CI and web-vitals budgets.

## 15. Device Experience

| Capability | Mobile (360–639) | Tablet (640–1023) | Desktop (1024+) |
|------------|------------------|-------------------|-----------------|
| Navigation | Drawer | Drawer (≤ 767) / bar | Full bar |
| Article layout | Single column | Single column | Article + rail |
| Product cards | 2-col grid | 3-col grid | 4-col grid |
| Tables (admin) | Card lists | Card lists | Full table |
| Filters | Drawer | Drawer/inline | Inline sidebar |
| Charts | Single-metric cards | 2-up charts | Full charts |
| Touch targets | ≥ 44 px | ≥ 44 px | ≥ 40 px |
| Test widths | 360 | 768 | 1024, 1440 |

**Rules:** mobile-first design, tablet inherits mobile layout for content and desktop for admin; no hover-dependent functionality on touch; desktop never receives mobile-only affordances (hamburger only when needed).

---

## 16. Verification — No AI functionality in the website UI

1. **The UI displays business information only.** Articles, products, pins, metrics, and settings are business-layer data.
2. **AI OS outputs render as content.** Approved articles, pin assets, and SEO metadata produced by the AI OS appear as normal business content — no "AI-generated" branding, no generation controls.
3. **AI OS insights are read-only.** Dashboard insight cards show AI OS-provided insights with an attribution label; they contain no prompts, no inputs, and no actions that call AI.
4. **The UI contains no AI machinery:** no chat widgets, no prompt boxes, no image/text generation tools, no model pickers, no "AI assistant" components, no direct calls to any model API.
5. **All AI communication flows through the Bridge** (12-api-contracts.md): UI → API → service → Bridge → AI OS. The UI never holds AI credentials.
6. **Review enforcement:** design review checklist rejects any component that invites generation, chat, or model interaction; CI dependency scanning rejects AI/LLM packages (Technology Stack §13).

## 17. Change process

- This design system is **permanent**. Changes require: a design review, an ADR where visual identity or token structure changes, a `CHANGELOG.md` entry, and approval by the Lead Product Designer and `@atoz/lead`.
- A change that introduces AI functionality into the UI is rejected outright under the Website Architecture Contract §1.
