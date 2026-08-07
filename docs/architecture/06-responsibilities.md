# 06 — Website Responsibilities

Each responsibility area is documented with the same template: **Purpose, Responsibilities, Owns, Never owns, AI OS APIs used, Future modules connecting.** Every area belongs to the business layer; the AI Brain's responsibilities are documented here only to mark boundaries.

---

## 1. Website (including articles and traffic)

- **Purpose:** Be the reader-facing business surface: fast, findable, and trustworthy.
- **Responsibilities:**
  - Render article, hub/category, product, and informational pages from published content.
  - Serve articles with clean URL policy, canonical tags, and structured data.
  - Capture and direct traffic (internal linking, hub pages, breadcrumbs, pagination).
  - Consent management and affiliate disclosure on every monetized page.
  - Performance budgets, accessibility, and mobile-first rendering.
- **Owns:** presentation, page composition, URL policy implementation, client instrumentation, site performance.
- **Never owns:** generating or editing content, keyword intelligence, business decisions, or any AI OS behavior.
- **AI OS APIs used:** none directly. Content arrives pre-approved via the content pipeline (`AIOS.Content.Intake` handled by the Bridge + Content Service).
- **Future modules connecting:** mobile app experience, newsletter/email surfaces, related-content modules (read-only from existing data), multilingual article views.

## 2. Pinterest

- **Purpose:** Turn Pinterest into a predictable traffic channel across 10+ accounts and multiple niches.
- **Responsibilities:**
  - Manage the account registry (one per niche), boards, and per-account configuration.
  - Schedule and publish pins through the Pinterest API with per-account rate-limit budgets.
  - Maintain the append-only pin ledger and pin-level attribution metadata (pin ID, account, niche, UTM).
  - Monitor publish health (failures, throttling, rejected pins) and expose it in the admin dashboard.
- **Owns:** accounts, boards, pin scheduling/publishing, pin records, attribution parameters, rate-limit budgets.
- **Never owns:** generating pin images or copy (AI Brain), pin strategy decisions, or performance analysis (analytics module).
- **AI OS APIs used:** `AIOS.Pinterest.Assets` (generated pin assets and copy variants) and `AIOS.Job.Request/Status` (for asset generation jobs).
- **Future modules connecting:** additional visual channels (if adopted as business channels), Pinterest webhook-driven moderation, account-level experiments.

## 3. Affiliate (including revenue)

- **Purpose:** Run the monetization machinery: catalog, links, attribution, and revenue accounting.
- **Responsibilities:**
  - Ingest and maintain the product catalog from affiliate networks (feeds and APIs).
  - Issue signed affiliate link tokens (`/go/{token}`) with click attribution and dedupe.
  - Record conversions and reconcile commissions into the commission ledger.
  - Enforce disclosure rules on every monetized page and link.
  - Produce revenue reporting inputs for analytics and the admin dashboard.
- **Owns:** product catalog, network mappings, link tokens, click and commission ledgers, disclosure metadata.
- **Never owns:** writing product copy/reviews (AI Brain), pricing decisions, payout execution, or AI OS logic.
- **AI OS APIs used:** `AIOS.SEO.Metadata` (page metadata), optionally `AIOS.Content.Intake` for approved product descriptions; insights on performance via `AIOS.Analytics.Insights`.
- **Future modules connecting:** new affiliate networks, payout/invoice providers, review and rating features, price-drop alerting (business rules only).

## 4. SEO

- **Purpose:** Make the site discoverable and measurable at millions-of-URL scale.
- **Responsibilities:**
  - Apply metadata (title, description, canonical, robots) from approved intelligence.
  - Generate sharded sitemaps and structured data (JSON-LD) on content events.
  - Enforce URL policy, internal linking rules, and performance budgets.
  - Monitor crawl health, index coverage, and Core Web Vitals; surface reports in the admin dashboard.
- **Owns:** SEO output production (tags, sitemaps, structured data), URL policy, SEO health reporting.
- **Never owns:** writing content, keyword research/insight generation, or ranking decisions (AI Brain work).
- **AI OS APIs used:** `AIOS.SEO.Metadata` (intelligence applied to pages), `AIOS.Analytics.Insights` (display-only recommendations).
- **Future modules connecting:** multilingual hreflang handling, site search, structured-data extensions (reviews, FAQs), crawl-API integrations.

## 5. Analytics

- **Purpose:** Provide the measurements the whole business runs on, at high event volume.
- **Responsibilities:**
  - Own the event schema (page views, pin clicks, affiliate clicks, conversions) and collection pipeline.
  - Build partitioned reporting read models from the event stream and warehouse.
  - Define KPIs (traffic, engagement, conversion, revenue, pin performance, SEO health) as code.
  - Power admin dashboards and scheduled reports; support exports.
- **Owns:** event schema, collection pipeline, warehouse, metric definitions, report read models.
- **Never owns:** predictions or insight generation (AI Brain), business decisions, or other modules' data.
- **AI OS APIs used:** `AIOS.Analytics.Insights` — insights are fetched and displayed read-only; the website never computes them itself.
- **Future modules connecting:** mobile app analytics, email attribution, channel-level attribution refinements (rule-based only; algorithmic attribution stays in the AI OS).

## 6. Admin Dashboard (including automation)

- **Purpose:** Give operators command over the business layer: content, Pinterest, affiliate, SEO, analytics, and settings.
- **Responsibilities:**
  - Review, approve, publish, and unpublish content; moderate scheduled pins; manage the catalog.
  - Schedule and monitor automations (publishing pipelines, pin queues, sitemap rebuilds, reports).
  - Configure niches, accounts, networks, and site settings.
  - Surface KPIs, revenue, SEO health, and AI OS-provided insights.
  - Maintain the audit trail of every operator action.
- **Owns:** admin UX, management commands, automation scheduling (business workflows only), settings, audit log.
- **Never owns:** automatic decision-making beyond explicitly configured rules, content generation, AI OS automation, or insight generation.
- **AI OS APIs used:** none directly. It displays AI OS-provided insights through the Analytics module.
- **Future modules connecting:** approval notifications (email/chat), export pipelines, role delegation, compliance reporting.

---

## Automation boundary

Automation in this architecture means **business workflow automation**: publishing pipelines, pin scheduling, sitemap rebuilds, report generation, and notifications. These are configured business rules owned by services and the admin dashboard. Anything that automates *thinking* (content generation, research, insights, strategy) belongs to the AI OS and is never implemented here.

## Cross-cutting responsibility rules

- **Traffic and revenue are outcomes**, not modules: traffic comes from SEO + Pinterest + content quality; revenue comes from the affiliate module. Both are measured by analytics.
- **Everything is niche-scoped.** Ten Pinterest accounts and multiple niches stay isolated in every area above.
- **No area calls the AI OS directly.** All AI OS use goes through the AI OS Bridge.
