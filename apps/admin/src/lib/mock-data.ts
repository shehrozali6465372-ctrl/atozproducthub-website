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
