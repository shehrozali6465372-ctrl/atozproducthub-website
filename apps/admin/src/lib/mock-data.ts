/**
 * M2 wireframe fixtures for the admin surface — presentation scaffolding only.
 * Read models arrive with Phases 9–11 (SEO, Analytics, Admin Dashboard).
 */

import type { AdminNavItem } from "@atoz/design-system";
import {
  BadgeDollarSign,
  BarChart3,
  DollarSign,
  FileText,
  Handshake,
  LayoutDashboard,
  Link2,
  MousePointerClick,
  Network,
  Package,
  Pin,
  Settings,
  Store,
  Workflow,
  Activity,
  FileClock,
  ScrollText,
} from "lucide-react";

export const NAV_ITEMS: AdminNavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard, section: "Operations" },
  { label: "Content", href: "/content", icon: FileText, section: "Operations" },
  { label: "Analytics", href: "/analytics", icon: BarChart3, section: "Operations" },
  { label: "Revenue", href: "/revenue", icon: DollarSign, section: "Operations" },
  { label: "Pinterest", href: "/pinterest", icon: Pin, section: "Channels" },
  {
    label: "Affiliate",
    href: "/affiliate",
    icon: Handshake,
    section: "Monetization",
    children: [
      { label: "Overview", href: "/affiliate", icon: Handshake },
      { label: "Networks", href: "/affiliate/networks", icon: Network },
      { label: "Merchants", href: "/affiliate/merchants", icon: Store },
      { label: "Products & offers", href: "/affiliate/products", icon: Package },
      { label: "Links", href: "/affiliate/links", icon: Link2 },
      { label: "Clicks", href: "/affiliate/clicks", icon: MousePointerClick },
      { label: "Conversions", href: "/affiliate/conversions", icon: BadgeDollarSign },
      { label: "Reconciliation", href: "/affiliate/reconciliation", icon: FileText },
    ],
  },
  {
    label: "Operations",
    href: "/ops",
    icon: Activity,
    section: "Governance",
    children: [
      { label: "Operations", href: "/ops", icon: Activity },
      { label: "Audit log", href: "/audit", icon: ScrollText },
      { label: "Logs", href: "/ops/logs", icon: FileClock },
    ],
  },
  { label: "Automation", href: "/automation", icon: Workflow, section: "Governance" },
  { label: "Settings", href: "/settings", icon: Settings, section: "Governance" },
];

export const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/content": "Content",
  "/content/new": "New Article",
  "/analytics": "Analytics",
  "/revenue": "Revenue",
  "/pinterest": "Pinterest",
  "/affiliate": "Affiliate",
  "/affiliate/networks": "Affiliate Networks",
  "/affiliate/merchants": "Affiliate Merchants",
  "/affiliate/products": "Affiliate Products",
  "/affiliate/links": "Affiliate Links",
  "/affiliate/clicks": "Affiliate Clicks",
  "/affiliate/conversions": "Affiliate Conversions",
  "/affiliate/reconciliation": "Affiliate Reconciliation",
  "/automation": "Automation",
  "/settings": "Settings",
  "/ops": "Operations",
  "/ops/logs": "Operations Logs",
  "/audit": "Audit Log",
};

export const NOTIFICATIONS = [
  {
    id: "n1",
    title: "Pin queue low",
    description: "Account 'kitchenhub' has 3 pins scheduled for next week.",
    timestamp: "12 min ago",
    tone: "warning" as const,
    read: false,
  },
  {
    id: "n2",
    title: "Commission reconciled",
    description: "Amazon August payout matched the ledger.",
    timestamp: "1 hr ago",
    tone: "success" as const,
    read: false,
  },
  {
    id: "n3",
    title: "Sitemap generated",
    description: "XML sitemap shard 7 of 12 refreshed.",
    timestamp: "3 hr ago",
    tone: "info" as const,
    read: true,
  },
];

export const DASHBOARD_KPIS = [
  { label: "Visitors (30d)", value: "128,430", delta: "+12.4%", trend: "up" as const, hint: "vs prev period" },
  { label: "Revenue (30d)", value: "$4,128.50", delta: "+8.1%", trend: "up" as const, hint: "all networks" },
  { label: "Pins published (30d)", value: "214", delta: "+5.0%", trend: "up" as const, hint: "10 accounts" },
  { label: "SEO health", value: "96/100", delta: "2 issues", trend: "down" as const, hint: "2 fixable" },
];

export const REVENUE_SERIES = [
  { label: "W1", revenue: 820, clicks: 4100 },
  { label: "W2", revenue: 910, clicks: 4380 },
  { label: "W3", revenue: 780, clicks: 4020 },
  { label: "W4", revenue: 1040, clicks: 4910 },
  { label: "W5", revenue: 1180, clicks: 5240 },
  { label: "W6", revenue: 1290, clicks: 5610 },
];

export const TRAFFIC_SERIES = [
  { label: "W1", pinterest: 5200, organic: 3100, direct: 1400 },
  { label: "W2", pinterest: 6100, organic: 3400, direct: 1500 },
  { label: "W3", pinterest: 5700, organic: 3600, direct: 1600 },
  { label: "W4", pinterest: 6900, organic: 3900, direct: 1700 },
  { label: "W5", pinterest: 7400, organic: 4100, direct: 1800 },
  { label: "W6", pinterest: 8100, organic: 4300, direct: 1900 },
];

export const TRAFFIC_SOURCES = [
  { name: "Pinterest", value: 58, color: "var(--color-danger-500)" },
  { name: "Organic search", value: 27, color: "var(--color-primary-500)" },
  { name: "Direct", value: 12, color: "var(--color-success-500)" },
  { name: "Other", value: 3, color: "var(--color-text-400)" },
];

export const TOP_PAGES = [
  { id: "p1", path: "/articles/kitchen-gadgets-guide", visits: 12400, conversion: "3.2%", status: "published" },
  { id: "p2", path: "/collections/best-kitchen-gadgets-2026", visits: 9800, conversion: "4.1%", status: "published" },
  { id: "p3", path: "/landing/kitchen-buys", visits: 8600, conversion: "2.9%", status: "published" },
  { id: "p4", path: "/products/everyday-chefs-knife", visits: 6400, conversion: "3.8%", status: "published" },
];

export const PIN_QUEUE = [
  { id: "pin1", title: "Kitchen gadgets worth buying", board: "Kitchen Buys", account: "kitchenhub", scheduled: "Aug 8, 09:00", status: "scheduled" as const },
  { id: "pin2", title: "Cast iron skillet guide", board: "Kitchen Buys", account: "kitchenhub", scheduled: "Aug 8, 14:00", status: "scheduled" as const },
  { id: "pin3", title: "Home office lighting tips", board: "Office Ideas", account: "workspacesetup", scheduled: "Aug 9, 09:00", status: "scheduled" as const },
  { id: "pin4", title: "One-bag travel packing cubes", board: "Travel Gear", account: "travelpicks", scheduled: "Aug 7, 18:00", status: "failed" as const },
];

export const AUTOMATION_RULES = [
  { id: "a1", name: "Pin queue replenishment", schedule: "Daily 06:00 UTC", status: "enabled" as const, lastRun: "Aug 7, 06:00" },
  { id: "a2", name: "Affiliate reconciliation", schedule: "Weekly Mon 04:00 UTC", status: "enabled" as const, lastRun: "Aug 4, 04:00" },
  { id: "a3", name: "XML sitemap refresh", schedule: "Daily 02:00 UTC", status: "enabled" as const, lastRun: "Aug 7, 02:00" },
  { id: "a4", name: "SEO health report", schedule: "Weekly Sun 08:00 UTC", status: "disabled" as const, lastRun: "Never" },
];

export const PIN_ACCOUNTS = [
  { id: "acct1", name: "kitchenhub", niche: "Kitchen", boards: 18, pins: 1240, rateLimit: "OK" },
  { id: "acct2", name: "workspacesetup", niche: "Office", boards: 12, pins: 860, rateLimit: "OK" },
  { id: "acct3", name: "travelpicks", niche: "Travel", boards: 14, pins: 1015, rateLimit: "Near limit" },
];

// ------------------------------------------------------------ CMS fixtures
// M4 admin CMS read models. Real records arrive from content-service through
// the API gateway; these keep the dashboard usable standalone (mock default).

export interface MockAdminArticle {
  id: string;
  nicheId: string;
  slug: string;
  title: string;
  excerpt: string;
  status: string;
  authorRef: string | null;
  editorRef: string | null;
  publishedAt: string | null;
  createdAt: string;
  updatedAt: string;
  primaryCategoryId: string | null;
  categoryIds: string[];
  tagIds: string[];
  versions: {
    id: string;
    versionNo: number;
    title: string;
    excerpt: string;
    changeSummary: string | null;
    createdBy: string | null;
    createdAt: string;
  }[];
}

export interface MockAdminNiche {
  id: string;
  name: string;
  slug: string;
  status: string;
  defaultCurrency: string | null;
}

export interface MockAdminCategory {
  id: string;
  nicheId: string;
  name: string;
  slug: string;
  description: string;
  status: string;
}

export interface MockAdminTag {
  id: string;
  nicheId: string;
  name: string;
  slug: string;
  status: string;
}

const MOCK_NICHE_ID = "11111111-1111-4111-8111-111111111111";

export const MOCK_ADMIN_NICHES: MockAdminNiche[] = [
  { id: MOCK_NICHE_ID, name: "Kitchen", slug: "kitchen", status: "active", defaultCurrency: "USD" },
];

export const MOCK_ADMIN_CATEGORIES: MockAdminCategory[] = [
  { id: "22222222-2222-4222-8222-222222222222", nicheId: MOCK_NICHE_ID, name: "Kitchen", slug: "kitchen", description: "Cookware, gadgets, and food-prep gear.", status: "active" },
  { id: "33333333-3333-4333-8333-333333333333", nicheId: MOCK_NICHE_ID, name: "Office", slug: "office", description: "Desks, chairs, lighting, and organization.", status: "active" },
];

export const MOCK_ADMIN_TAGS: MockAdminTag[] = [
  { id: "44444444-4444-4444-8444-444444444444", nicheId: MOCK_NICHE_ID, name: "Buying Guide", slug: "buying-guide", status: "active" },
  { id: "55555555-5555-4555-8555-555555555555", nicheId: MOCK_NICHE_ID, name: "Kitchen", slug: "kitchen", status: "active" },
];

export const MOCK_ADMIN_ARTICLES: MockAdminArticle[] = [
  {
    id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    nicheId: MOCK_NICHE_ID,
    slug: "sample-article",
    title: "The Kitchen Gadgets Guide: What's Actually Worth Buying",
    excerpt: "A practical, honest look at the kitchen tools that earn their counter space.",
    status: "published",
    authorRef: "author@atozproducthub.com",
    editorRef: "editor@atozproducthub.com",
    publishedAt: "2026-08-02T09:00:00Z",
    createdAt: "2026-07-20T10:00:00Z",
    updatedAt: "2026-08-02T09:00:00Z",
    primaryCategoryId: "22222222-2222-4222-8222-222222222222",
    categoryIds: ["22222222-2222-4222-8222-222222222222"],
    tagIds: ["55555555-5555-4555-8555-555555555555", "44444444-4444-4444-8444-444444444444"],
    versions: [
      {
        id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        versionNo: 2,
        title: "The Kitchen Gadgets Guide: What's Actually Worth Buying",
        excerpt: "A practical, honest look at the kitchen tools that earn their counter space.",
        changeSummary: "Added 2026 price updates.",
        createdBy: "editor@atozproducthub.com",
        createdAt: "2026-08-02T09:00:00Z",
      },
      {
        id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        versionNo: 1,
        title: "The Kitchen Gadgets Guide",
        excerpt: "A practical look at kitchen tools.",
        changeSummary: "Initial draft.",
        createdBy: "author@atozproducthub.com",
        createdAt: "2026-07-20T10:00:00Z",
      },
    ],
  },
  {
    id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
    nicheId: MOCK_NICHE_ID,
    slug: "home-office-essentials",
    title: "Home Office Essentials: Setup That Survives the 9-to-5",
    excerpt: "Chairs, lighting, and desk organization upgrades.",
    status: "draft",
    authorRef: "author@atozproducthub.com",
    editorRef: null,
    publishedAt: null,
    createdAt: "2026-07-26T10:00:00Z",
    updatedAt: "2026-07-26T10:00:00Z",
    primaryCategoryId: "33333333-3333-4333-8333-333333333333",
    categoryIds: ["33333333-3333-4333-8333-333333333333"],
    tagIds: ["44444444-4444-4444-8444-444444444444"],
    versions: [],
  },
  {
    id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
    nicheId: MOCK_NICHE_ID,
    slug: "travel-pack-light",
    title: "Pack Light, Pack Right: Travel Gear for Carry-On-Only Trips",
    excerpt: "Packing systems that turn one-bag trips from stressful to effortless.",
    status: "review",
    authorRef: "author@atozproducthub.com",
    editorRef: null,
    publishedAt: null,
    createdAt: "2026-07-12T10:00:00Z",
    updatedAt: "2026-07-28T10:00:00Z",
    primaryCategoryId: null,
    categoryIds: [],
    tagIds: [],
    versions: [],
  },
];

export function mockArticleBody(article: MockAdminArticle): string {
  if (article.id === "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa") {
    return [
      "Every year, thousands of new kitchen gadgets promise to change the way you cook. Most of them end up in a drawer.",
      "Start with the essentials: a quality chef's knife, a properly seasoned pan, and a thermometer you trust.",
    ].join("\n\n");
  }
  return "Draft content will be written here by the AI Content OS and reviewed by editors.\n\nSecond paragraph placeholder.";
}

// ------------------------------------------------------------- affiliate
export const MOCK_AFFILIATE_NETWORKS = [
  {
    id: "nw-1",
    code: "amazon",
    name: "Amazon Associates",
    status: "active",
    feedType: "csv",
    webhookSecretRef: "vault://affiliate/amazon/webhook-secret",
    settingsJson: "{}",
    createdAt: "2026-06-01T08:00:00Z",
    updatedAt: "2026-08-01T08:00:00Z",
  },
  {
    id: "nw-2",
    code: "impact",
    name: "Impact Radius",
    status: "active",
    feedType: "api",
    webhookSecretRef: "vault://affiliate/impact/webhook-secret",
    settingsJson: "{}",
    createdAt: "2026-06-15T08:00:00Z",
    updatedAt: "2026-08-01T08:00:00Z",
  },
];

export const MOCK_AFFILIATE_MERCHANTS = [
  {
    id: "m-1",
    networkId: "nw-1",
    remoteMerchantId: "amz-merchant-1",
    name: "Acme Kitchen Co.",
    status: "active",
    commissionTermsJson: '{"rate":"5%"}',
  },
  {
    id: "m-2",
    networkId: "nw-2",
    remoteMerchantId: "imp-merchant-2",
    name: "Trail & Travel",
    status: "active",
    commissionTermsJson: '{"rate":"8%"}',
  },
];

export const MOCK_AFFILIATE_CATEGORIES = [
  {
    id: "ac-1",
    nicheId: MOCK_NICHE_ID,
    parentId: null,
    name: "Cookware",
    slug: "cookware",
    path: null,
    sortOrder: 1,
    status: "active",
  },
];

export const MOCK_AFFILIATE_PRODUCTS = [
  {
    id: "p-1",
    nicheId: MOCK_NICHE_ID,
    merchantId: "m-1",
    sku: "SKU-PAN-1",
    slug: "stainless-pan",
    name: "Stainless Steel Pan",
    excerpt: "A reliable do-everything pan.",
    priceCents: 4500,
    currency: "USD",
    status: "active",
    checksum: "abc123",
    lastFeedAt: "2026-08-02T08:00:00Z",
    deletedAt: null,
    createdAt: "2026-07-01T08:00:00Z",
    updatedAt: "2026-08-02T08:00:00Z",
  },
  {
    id: "p-2",
    nicheId: MOCK_NICHE_ID,
    merchantId: "m-2",
    sku: "SKU-BAG-1",
    slug: "travel-backpack",
    name: "Travel Backpack 28L",
    excerpt: "Carry-on sized with laptop sleeve.",
    priceCents: 12900,
    currency: "USD",
    status: "draft",
    checksum: "def456",
    lastFeedAt: null,
    deletedAt: null,
    createdAt: "2026-07-10T08:00:00Z",
    updatedAt: "2026-07-20T08:00:00Z",
  },
];

export const MOCK_AFFILIATE_LINKS = [
  {
    id: "l-1",
    nicheId: MOCK_NICHE_ID,
    productId: "p-1",
    networkId: "nw-1",
    networkLinkUrl: "https://partner.example.com/go?pid=100",
    defaultCommissionRate: "5%",
    status: "active",
    disclosureRequired: true,
    createdAt: "2026-07-01T08:00:00Z",
    updatedAt: "2026-08-02T08:00:00Z",
  },
];

export const MOCK_AFFILIATE_CLICKS = [
  {
    id: "c-1",
    nicheId: MOCK_NICHE_ID,
    linkTokenId: "t-1",
    attributionId: "a-1",
    revenueTransactionId: null,
    clickedAt: "2026-08-08T14:22:00Z",
    ipHash: "3f4a…",
    userAgentHash: "9b2c…",
    referrer: "https://pinterest.com/pin/123",
    isBot: false,
    fraudFlag: false,
  },
];

export const MOCK_AFFILIATE_REVENUE = [
  {
    id: "r-1",
    nicheId: MOCK_NICHE_ID,
    networkId: "nw-1",
    affiliateLinkId: "l-1",
    affiliateClickId: "c-1",
    networkTransactionId: "ntx-1001",
    grossCents: 50000,
    commissionCents: 2500,
    currency: "USD",
    status: "pending",
    occurredAt: "2026-08-09T09:00:00Z",
    reconciledAt: null,
    createdAt: "2026-08-09T09:00:05Z",
  },
];

export const MOCK_AFFILIATE_RECONCILIATIONS = [
  {
    id: "rc-1",
    nicheId: MOCK_NICHE_ID,
    networkId: "nw-1",
    reportedAt: "2026-08-08T00:00:00Z",
    expectedTotalCents: 2500,
    actualTotalCents: 2500,
    deltaCents: 0,
    status: "matched",
    reportRef: "amazon-2026-08-08.csv",
    createdAt: "2026-08-09T03:00:00Z",
  },
];

export const MOCK_AFFILIATE_SUMMARIES = [
  {
    id: "s-1",
    nicheId: MOCK_NICHE_ID,
    networkId: "nw-1",
    summaryDate: "2026-08-09",
    clicks: 128,
    sales: 3,
    grossCents: 150000,
    commissionCents: 7500,
    currency: "USD",
  },
];

export const MOCK_AFFILIATE_DASHBOARD = {
  totalCommissionCents: 7500,
  approvedCommissionCents: 2500,
  pendingCommissionCents: 5000,
  paidCommissionCents: 0,
  transactionCount: 3,
  clickCount: 128,
};

// ---------------------------------------------------------------- M9 ops data
export const OPS_OVERVIEW = {
  failedQueueItems: 1,
  failedWebhooks: 2,
  failedOperations: 3,
  failedJobRuns: 0,
  openNotifications: 4,
  auditEntries: 1284,
  queues: { queued: 12, claimed: 2, done: 1041, failed: 1 },
};

export interface MockServiceStatus {
  id: string;
  name: string;
  status: "ok" | "degraded" | "down" | "unknown";
  version: string | null;
  latencyMs: number | null;
  error: string | null;
}

export const SYSTEM_STATUS: { overall: string; services: MockServiceStatus[] } = {
  overall: "degraded",
  services: [
    { id: "admin-service", name: "admin-service", status: "ok", version: "0.9.0", latencyMs: 4, error: null },
    { id: "content-service", name: "content-service", status: "ok", version: "0.4.0", latencyMs: 12, error: null },
    { id: "affiliate-service", name: "affiliate-service", status: "ok", version: "0.5.0", latencyMs: 9, error: null },
    { id: "pinterest-service", name: "pinterest-service", status: "degraded", version: "0.6.0", latencyMs: 0, error: "rate limited (org_write budget exhausted)" },
    { id: "seo-service", name: "seo-service", status: "ok", version: "0.7.0", latencyMs: 15, error: null },
    { id: "analytics-service", name: "analytics-service", status: "ok", version: "0.8.0", latencyMs: 21, error: null },
  ],
};

export const ISOLATION_CHECK = {
  ok: true,
  checks: [
    { table: "audit", rows: 1284, orphaned: [] },
    { table: "queue", rows: 1056, orphaned: [] },
    { table: "webhook", rows: 412, orphaned: [] },
    { table: "operation", rows: 2330, orphaned: [] },
  ],
};

export const AUDIT_LOGS = [
  {
    id: "audit-1",
    nicheId: "niche-1",
    adminUserId: "op-1",
    apiKeyId: null,
    action: "publish",
    entityType: "article",
    entityId: "art-101",
    beforeJson: null,
    afterJson: '{"status":"published"}',
    requestId: "req-001",
    occurredAt: "2026-08-12T09:04:00Z",
  },
  {
    id: "audit-2",
    nicheId: "niche-1",
    adminUserId: "op-2",
    apiKeyId: null,
    action: "retry",
    entityType: "queue_item",
    entityId: "q-55",
    beforeJson: '{"state":"failed"}',
    afterJson: '{"state":"queued"}',
    requestId: "req-002",
    occurredAt: "2026-08-12T08:51:00Z",
  },
  {
    id: "audit-3",
    nicheId: null,
    adminUserId: "op-1",
    apiKeyId: "ak-9",
    action: "assign",
    entityType: "role",
    entityId: "pinterest_operator",
    beforeJson: null,
    afterJson: '{"admin_user_id":"op-3"}',
    requestId: "req-003",
    occurredAt: "2026-08-12T08:12:00Z",
  },
];

export const QUEUE_ITEMS = [
  {
    id: "q-1",
    nicheId: "niche-1",
    queue: "pins",
    payloadRef: "pin-441",
    state: "queued",
    attempts: 0,
    maxAttempts: 5,
    runAt: "2026-08-12T10:00:00Z",
    error: null,
  },
  {
    id: "q-55",
    nicheId: "niche-1",
    queue: "pins",
    payloadRef: "pin-102",
    state: "failed",
    attempts: 5,
    maxAttempts: 5,
    runAt: "2026-08-12T07:30:00Z",
    error: "pinterest 429: org_write rate limit exceeded",
  },
  {
    id: "q-2",
    nicheId: "niche-2",
    queue: "seo-sitemap",
    payloadRef: "sitemap-2026-08",
    state: "queued",
    attempts: 1,
    maxAttempts: 3,
    runAt: "2026-08-12T11:00:00Z",
    error: null,
  },
];

export const WEBHOOK_LOGS = [
  {
    id: "wh-1",
    nicheId: "niche-1",
    source: "affiliate",
    eventId: "evt-a-1",
    status: "processed",
    receivedAt: "2026-08-12T09:40:00Z",
    error: null,
  },
  {
    id: "wh-2",
    nicheId: "niche-1",
    source: "pinterest",
    eventId: "evt-p-1",
    status: "failed",
    receivedAt: "2026-08-12T09:31:00Z",
    error: "signature verification failed",
  },
  {
    id: "wh-3",
    nicheId: null,
    source: "content",
    eventId: "evt-c-1",
    status: "processed",
    receivedAt: "2026-08-12T09:00:00Z",
    error: null,
  },
];

export const OPERATION_LOGS = [
  {
    id: "op-1",
    nicheId: "niche-1",
    operation: "content.publish",
    entityType: "article",
    entityId: "art-101",
    status: "succeeded",
    message: "Published article art-101",
    occurredAt: "2026-08-12T09:04:00Z",
  },
  {
    id: "op-2",
    nicheId: "niche-1",
    operation: "pinterest.pin_publish",
    entityType: "pin",
    entityId: "pin-102",
    status: "failed",
    message: "pinterest 429: org_write rate limit exceeded",
    occurredAt: "2026-08-12T07:30:00Z",
  },
  {
    id: "op-3",
    nicheId: "niche-2",
    operation: "affiliate.revenue_attributed",
    entityType: "conversion",
    entityId: "conv-7",
    status: "succeeded",
    message: "Commission attributed",
    occurredAt: "2026-08-12T08:15:00Z",
  },
];

export const SCHEDULED_JOBS = [
  {
    id: "job-1",
    nicheId: null,
    jobKey: "analytics.daily-rollup",
    cronExpr: "0 2 * * *",
    queue: "rollups",
    handler: "analytics-service.rollup",
    status: "enabled",
    nextRunAt: "2026-08-13T02:00:00Z",
  },
  {
    id: "job-2",
    nicheId: null,
    jobKey: "seo.sitemap-rebuild",
    cronExpr: "0 4 * * *",
    queue: "seo",
    handler: "seo-service.sitemap",
    status: "enabled",
    nextRunAt: "2026-08-13T04:00:00Z",
  },
  {
    id: "job-3",
    nicheId: null,
    jobKey: "affiliate.reconcile",
    cronExpr: "0 6 * * 1",
    queue: "affiliate",
    handler: "affiliate-service.reconcile",
    status: "enabled",
    nextRunAt: "2026-08-17T06:00:00Z",
  },
];

export const JOB_RUNS = [
  {
    id: "run-1",
    scheduledJobId: "job-1",
    status: "success",
    attempts: 1,
    runAt: "2026-08-12T02:00:00Z",
    startedAt: "2026-08-12T02:00:01Z",
    finishedAt: "2026-08-12T02:00:42Z",
    error: null,
  },
  {
    id: "run-2",
    scheduledJobId: "job-2",
    status: "failed",
    attempts: 2,
    runAt: "2026-08-12T04:00:00Z",
    startedAt: "2026-08-12T04:00:01Z",
    finishedAt: "2026-08-12T04:00:05Z",
    error: "typesense connection refused",
  },
];

export const OPS_NOTIFICATIONS = [
  {
    id: "n-1",
    nicheId: "niche-1",
    recipientId: "op-1",
    type: "failure",
    title: "Pin publish failed",
    body: "pin-102 exceeded the Pinterest org_write rate limit.",
    status: "unread",
    createdAt: "2026-08-12T07:30:00Z",
    readAt: null,
  },
  {
    id: "n-2",
    nicheId: null,
    recipientId: "op-1",
    type: "report.ready",
    title: "Daily analytics report ready",
    body: "Rollup for 2026-08-11 is available.",
    status: "read",
    createdAt: "2026-08-12T02:05:00Z",
    readAt: "2026-08-12T08:00:00Z",
  },
];
