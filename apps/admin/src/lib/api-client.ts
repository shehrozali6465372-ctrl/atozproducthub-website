import {
  AUTOMATION_RULES,
  DASHBOARD_KPIS,
  MOCK_AFFILIATE_CATEGORIES,
  MOCK_AFFILIATE_CLICKS,
  MOCK_AFFILIATE_DASHBOARD,
  MOCK_AFFILIATE_LINKS,
  MOCK_AFFILIATE_MERCHANTS,
  MOCK_AFFILIATE_NETWORKS,
  MOCK_AFFILIATE_PRODUCTS,
  MOCK_AFFILIATE_RECONCILIATIONS,
  MOCK_AFFILIATE_REVENUE,
  MOCK_AFFILIATE_SUMMARIES,
  MOCK_ADMIN_ARTICLES,
  MOCK_ADMIN_CATEGORIES,
  MOCK_ADMIN_NICHES,
  MOCK_ADMIN_TAGS,
  NOTIFICATIONS,
  PAGE_TITLES,
  PIN_ACCOUNTS,
  PIN_QUEUE,
  REVENUE_SERIES,
  TOP_PAGES,
  TRAFFIC_SERIES,
  TRAFFIC_SOURCES,
  mockArticleBody,
  type MockAdminArticle,
} from "./mock-data";

/**
 * Typed admin API client.
 *
 * M4: the content namespace talks to content-service admin routes when
 * NEXT_PUBLIC_CONTENT_API_BASE_URL is set. The caller provides tenancy and
 * auth context (X-Niche-Id + Bearer JWT) — read from localStorage when the
 * operator signed in, or from NEXT_PUBLIC_NICHE_ID / NEXT_PUBLIC_ADMIN_TOKEN
 * for local development. Without the env var the client keeps the M2 mock
 * fixtures, so the admin app renders standalone.
 *
 * No AI functionality exists here: the CMS only edits content produced by
 * the AI OS and delivered through the AI OS Bridge (Website Contract §4).
 */

export interface Kpi {
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
  hint: string;
}

// ------------------------------------------------------------- CMS read models
export interface AdminArticle {
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
}

export interface AdminCategoryRef {
  id: string;
  slug: string;
  name: string;
  isPrimary: boolean;
}

export interface AdminTagRef {
  id: string;
  slug: string;
  name: string;
}

export interface AdminVersion {
  id: string;
  versionNo: number;
  title: string;
  excerpt: string;
  changeSummary: string | null;
  createdBy: string | null;
  createdAt: string;
}

export interface AdminArticleDetail extends AdminArticle {
  primaryCategoryId: string | null;
  body: string;
  categories: AdminCategoryRef[];
  tags: AdminTagRef[];
  versions: AdminVersion[];
}

export interface AdminNiche {
  id: string;
  name: string;
  slug: string;
  status: string;
  defaultCurrency: string | null;
}

export interface AdminCategory {
  id: string;
  nicheId: string;
  name: string;
  slug: string;
  description: string;
  status: string;
}

export interface AdminTag {
  id: string;
  nicheId: string;
  name: string;
  slug: string;
  status: string;
}

export type LifecycleAction =
  | "submit"
  | "approve"
  | "reject"
  | "publish"
  | "unpublish"
  | "archive"
  | "restore";

export interface ArticlePayload {
  title: string;
  excerpt: string;
  body: string;
  slug?: string;
  categoryIds: string[];
  primaryCategoryId: string | null;
  tagIds: string[];
  changeSummary?: string;
}

export interface AdminApiClient {
  dashboard: {
    getKpis(): Promise<Kpi[]>;
    getRevenueSeries(): Promise<typeof REVENUE_SERIES>;
    getTrafficSeries(): Promise<typeof TRAFFIC_SERIES>;
    getTopPages(): Promise<typeof TOP_PAGES>;
    getNotifications(): Promise<typeof NOTIFICATIONS>;
  };
  analytics: {
    getTrafficSources(): Promise<typeof TRAFFIC_SOURCES>;
  };
  pinterest: {
    getAccounts(): Promise<typeof PIN_ACCOUNTS>;
    getPinQueue(): Promise<typeof PIN_QUEUE>;
  };
  automation: {
    getRules(): Promise<typeof AUTOMATION_RULES>;
  };
  content: {
    listNiches(): Promise<AdminNiche[]>;
    listCategories(): Promise<AdminCategory[]>;
    listTags(): Promise<AdminTag[]>;
    listArticles(status?: string): Promise<AdminArticle[]>;
    getArticle(id: string): Promise<AdminArticleDetail | null>;
    createArticle(payload: ArticlePayload): Promise<AdminArticle>;
    updateArticle(id: string, payload: ArticlePayload): Promise<AdminArticle>;
    deleteArticle(id: string): Promise<void>;
    transition(id: string, action: LifecycleAction): Promise<AdminArticle>;
  };
  affiliate: {
    listNetworks(): Promise<AdminNetwork[]>;
    createNetwork(payload: AdminNetworkCreate): Promise<AdminNetwork>;
    listMerchants(): Promise<AdminMerchant[]>;
    listCategories(): Promise<AdminProductCategory[]>;
    listProducts(): Promise<AdminProduct[]>;
    listLinks(): Promise<AdminAffiliateLink[]>;
    listClicks(): Promise<AdminClick[]>;
    listRevenue(status?: string): Promise<AdminRevenueTransaction[]>;
    transitionCommission(id: string, action: "approve" | "reject" | "mark_paid"): Promise<AdminRevenueTransaction>;
    listReconciliations(): Promise<AdminReconciliation[]>;
    listSummaries(): Promise<AdminRevenueSummary[]>;
    revenueDashboard(): Promise<AdminRevenueDashboard>;
  };
}

// -------------------------------------------------------- affiliate read models
export interface AdminNetwork {
  id: string;
  code: string;
  name: string;
  status: string;
  feedType: string;
  webhookSecretRef: string;
  settingsJson: string;
  createdAt: string;
  updatedAt: string;
}

export interface AdminNetworkCreate {
  code: string;
  name: string;
  status?: string;
  feedType?: string;
}

export interface AdminMerchant {
  id: string;
  networkId: string;
  remoteMerchantId: string;
  name: string;
  status: string;
  commissionTermsJson: string;
}

export interface AdminProductCategory {
  id: string;
  nicheId: string;
  parentId: string | null;
  name: string;
  slug: string;
  path: string | null;
  sortOrder: number;
  status: string;
}

export interface AdminProduct {
  id: string;
  nicheId: string;
  merchantId: string;
  sku: string;
  slug: string;
  name: string;
  excerpt: string;
  priceCents: number;
  currency: string;
  status: string;
  checksum: string | null;
  lastFeedAt: string | null;
  deletedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface AdminAffiliateLink {
  id: string;
  nicheId: string;
  productId: string;
  networkId: string;
  networkLinkUrl: string;
  defaultCommissionRate: string;
  status: string;
  disclosureRequired: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AdminClick {
  id: string;
  nicheId: string;
  linkTokenId: string;
  attributionId: string | null;
  revenueTransactionId: string | null;
  clickedAt: string;
  ipHash: string | null;
  userAgentHash: string | null;
  referrer: string | null;
  isBot: boolean;
  fraudFlag: boolean;
}

export interface AdminRevenueTransaction {
  id: string;
  nicheId: string;
  networkId: string;
  affiliateLinkId: string;
  affiliateClickId: string | null;
  networkTransactionId: string;
  grossCents: number;
  commissionCents: number;
  currency: string;
  status: string;
  occurredAt: string;
  reconciledAt: string | null;
  createdAt: string;
}

export interface AdminReconciliation {
  id: string;
  nicheId: string;
  networkId: string;
  reportedAt: string;
  expectedTotalCents: number;
  actualTotalCents: number;
  deltaCents: number;
  status: string;
  reportRef: string | null;
  createdAt: string;
}

export interface AdminRevenueSummary {
  id: string;
  nicheId: string;
  networkId: string | null;
  summaryDate: string;
  clicks: number;
  sales: number;
  grossCents: number;
  commissionCents: number;
  currency: string;
}

export interface AdminRevenueDashboard {
  totalCommissionCents: number;
  approvedCommissionCents: number;
  pendingCommissionCents: number;
  paidCommissionCents: number;
  transactionCount: number;
  clickCount: number;
}

// ------------------------------------------------------------------ mock mode
const delay = <T>(value: T): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), 0));

function toMockDetail(article: MockAdminArticle): AdminArticleDetail {
  const categories = MOCK_ADMIN_CATEGORIES.filter((category) =>
    article.categoryIds.includes(category.id),
  ).map((category) => ({
    id: category.id,
    slug: category.slug,
    name: category.name,
    isPrimary: category.id === article.primaryCategoryId,
  }));
  const tags = MOCK_ADMIN_TAGS.filter((tag) => article.tagIds.includes(tag.id)).map((tag) => ({
    id: tag.id,
    slug: tag.slug,
    name: tag.name,
  }));
  return {
    id: article.id,
    nicheId: article.nicheId,
    slug: article.slug,
    title: article.title,
    excerpt: article.excerpt,
    status: article.status,
    authorRef: article.authorRef,
    editorRef: article.editorRef,
    publishedAt: article.publishedAt,
    createdAt: article.createdAt,
    updatedAt: article.updatedAt,
    primaryCategoryId: article.primaryCategoryId,
    body: mockArticleBody(article),
    categories,
    tags,
    versions: article.versions,
  };
}

const mockContentClient = {
  listNiches: () => delay(MOCK_ADMIN_NICHES),
  listCategories: () => delay(MOCK_ADMIN_CATEGORIES),
  listTags: () => delay(MOCK_ADMIN_TAGS),
  listArticles: (status?: string) =>
    delay(status ? MOCK_ADMIN_ARTICLES.filter((article) => article.status === status) : MOCK_ADMIN_ARTICLES),
  getArticle: (id: string) => {
    const article = MOCK_ADMIN_ARTICLES.find((item) => item.id === id);
    return delay(article ? toMockDetail(article) : null);
  },
  createArticle: (payload: ArticlePayload) =>
    delay({
      id: crypto.randomUUID(),
      nicheId: MOCK_ADMIN_NICHES[0].id,
      slug: payload.slug ?? payload.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
      title: payload.title,
      excerpt: payload.excerpt,
      status: "draft",
      authorRef: "admin@atozproducthub.com",
      editorRef: null,
      publishedAt: null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }),
  updateArticle: (_id: string, payload: ArticlePayload) =>
    delay({
      id: _id,
      nicheId: MOCK_ADMIN_NICHES[0].id,
      slug: payload.slug ?? "article",
      title: payload.title,
      excerpt: payload.excerpt,
      status: "draft",
      authorRef: "admin@atozproducthub.com",
      editorRef: null,
      publishedAt: null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }),
  deleteArticle: () => delay(undefined),
  transition: (_id: string, action: LifecycleAction) => {
    const article = MOCK_ADMIN_ARTICLES[0];
    const next: Partial<Record<LifecycleAction, string>> = {
      submit: "review",
      approve: "published",
      reject: "draft",
      publish: "published",
      unpublish: "unpublished",
      archive: "archived",
      restore: "draft",
    };
    return delay({ ...article, status: next[action] ?? article.status });
  },
};

const mockAffiliateClient = {
  listNetworks: () => delay(MOCK_AFFILIATE_NETWORKS),
  createNetwork: (payload: AdminNetworkCreate) =>
    delay({
      id: crypto.randomUUID(),
      code: payload.code,
      name: payload.name,
      status: payload.status ?? "active",
      feedType: payload.feedType ?? "csv",
      webhookSecretRef: "",
      settingsJson: "{}",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }),
  listMerchants: () => delay(MOCK_AFFILIATE_MERCHANTS),
  listCategories: () => delay(MOCK_AFFILIATE_CATEGORIES),
  listProducts: () => delay(MOCK_AFFILIATE_PRODUCTS),
  listLinks: () => delay(MOCK_AFFILIATE_LINKS),
  listClicks: () => delay(MOCK_AFFILIATE_CLICKS),
  listRevenue: (status?: string) =>
    delay(
      (
        status
          ? MOCK_AFFILIATE_REVENUE.filter((row) => row.status === status)
          : MOCK_AFFILIATE_REVENUE
      ).map((row) => ({ ...row })),
    ),
  transitionCommission: (id: string, action: "approve" | "reject" | "mark_paid") => {
    const next: Record<string, string> = { approve: "approved", reject: "rejected", mark_paid: "paid" };
    const row = MOCK_AFFILIATE_REVENUE.find((item) => item.id === id) ?? MOCK_AFFILIATE_REVENUE[0];
    row.status = next[action];
    return delay(row);
  },
  listReconciliations: () => delay(MOCK_AFFILIATE_RECONCILIATIONS),
  listSummaries: () => delay(MOCK_AFFILIATE_SUMMARIES),
  revenueDashboard: () => delay(MOCK_AFFILIATE_DASHBOARD),
};

const mockAdminApiClient: AdminApiClient = {
  dashboard: {
    getKpis: () => delay(DASHBOARD_KPIS),
    getRevenueSeries: () => delay(REVENUE_SERIES),
    getTrafficSeries: () => delay(TRAFFIC_SERIES),
    getTopPages: () => delay(TOP_PAGES),
    getNotifications: () => delay(NOTIFICATIONS),
  },
  analytics: {
    getTrafficSources: () => delay(TRAFFIC_SOURCES),
  },
  pinterest: {
    getAccounts: () => delay(PIN_ACCOUNTS),
    getPinQueue: () => delay(PIN_QUEUE),
  },
  automation: {
    getRules: () => delay(AUTOMATION_RULES),
  },
  content: mockContentClient,
  affiliate: mockAffiliateClient,
};

// ------------------------------------------------------------------ live mode
const CONTENT_API_BASE = process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL ?? "";
const AFFILIATE_API_BASE = process.env.NEXT_PUBLIC_AFFILIATE_API_BASE_URL ?? "";

interface LiveArticleDto {
  id: string;
  niche_id: string;
  slug: string;
  title: string;
  excerpt: string;
  status: string;
  author_ref: string | null;
  editor_ref: string | null;
  primary_category_id: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

interface LiveArticleDetailDto {
  article: LiveArticleDto;
  categories: { id: string; slug: string; name: string; is_primary: boolean }[];
  tags: { id: string; slug: string; name: string }[];
  versions: {
    id: string;
    version_no: number;
    title: string;
    excerpt: string;
    content_ref: string;
    checksum: string;
    change_summary: string | null;
    created_by: string | null;
    created_at: string;
  }[];
}

interface LivePageDto<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

function liveHeaders(): HeadersInit {
  const token =
    (typeof window !== "undefined" ? window.localStorage.getItem("atoz_admin_token") : null) ??
    (process.env.NEXT_PUBLIC_ADMIN_TOKEN ?? "");
  const nicheId =
    (typeof window !== "undefined" ? window.localStorage.getItem("atoz_niche_id") : null) ??
    (process.env.NEXT_PUBLIC_NICHE_ID ?? "");
  const headers: Record<string, string> = { Accept: "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (nicheId) headers["X-Niche-Id"] = nicheId;
  return headers;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${CONTENT_API_BASE}${path}`, {
    ...init,
    headers: { ...liveHeaders(), ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
  });
  if (!response.ok) {
    throw new Error(`Admin content API request failed: ${response.status} ${response.statusText}`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function toAdminArticle(dto: LiveArticleDto): AdminArticle {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    slug: dto.slug,
    title: dto.title,
    excerpt: dto.excerpt,
    status: dto.status,
    authorRef: dto.author_ref,
    editorRef: dto.editor_ref,
    publishedAt: dto.published_at,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

function toAdminDetail(dto: LiveArticleDetailDto): AdminArticleDetail {
  return {
    ...toAdminArticle(dto.article),
    primaryCategoryId: dto.article.primary_category_id,
    body: "",
    categories: dto.categories.map((category) => ({
      id: category.id,
      slug: category.slug,
      name: category.name,
      isPrimary: category.is_primary,
    })),
    tags: dto.tags.map((tag) => ({ id: tag.id, slug: tag.slug, name: tag.name })),
    versions: dto.versions.map((version) => ({
      id: version.id,
      versionNo: version.version_no,
      title: version.title,
      excerpt: version.excerpt,
      changeSummary: version.change_summary,
      createdBy: version.created_by,
      createdAt: version.created_at,
    })),
  };
}

function toArticlePayload(payload: ArticlePayload) {
  return {
    title: payload.title,
    excerpt: payload.excerpt,
    body: payload.body,
    slug: payload.slug || undefined,
    category_ids: payload.categoryIds,
    primary_category_id: payload.primaryCategoryId,
    tag_ids: payload.tagIds,
    change_summary: payload.changeSummary,
  };
}

const liveContentClient = {
  listNiches: () =>
    fetchJson<{ id: string; name: string; slug: string; status: string; default_currency: string | null }[]>("/api/v1/admin/niches").then(
      (items) =>
        items.map((item) => ({
          id: item.id,
          name: item.name,
          slug: item.slug,
          status: item.status,
          defaultCurrency: item.default_currency,
        })),
    ),
  listCategories: () =>
    fetchJson<{ id: string; niche_id: string; name: string; slug: string; description: string; status: string }[]>("/api/v1/admin/categories").then(
      (items) =>
        items.map((item) => ({
          id: item.id,
          nicheId: item.niche_id,
          name: item.name,
          slug: item.slug,
          description: item.description,
          status: item.status,
        })),
    ),
  listTags: () =>
    fetchJson<{ id: string; niche_id: string; name: string; slug: string; status: string }[]>("/api/v1/admin/tags").then(
      (items) =>
        items.map((item) => ({
          id: item.id,
          nicheId: item.niche_id,
          name: item.name,
          slug: item.slug,
          status: item.status,
        })),
    ),
  listArticles: (status?: string) => {
    const query = new URLSearchParams({ page_size: "100" });
    if (status) query.set("status", status);
    return fetchJson<LivePageDto<LiveArticleDto>>(`/api/v1/admin/articles?${query.toString()}`).then(
      (page) => page.items.map(toAdminArticle),
    );
  },
  getArticle: async (id: string) => {
    try {
      const detail = await fetchJson<LiveArticleDetailDto>(`/api/v1/admin/articles/${id}`);
      return toAdminDetail(detail);
    } catch {
      return null;
    }
  },
  createArticle: (payload: ArticlePayload) =>
    fetchJson<LiveArticleDto>("/api/v1/admin/articles", {
      method: "POST",
      body: JSON.stringify(toArticlePayload(payload)),
    }).then(toAdminArticle),
  updateArticle: (id: string, payload: ArticlePayload) =>
    fetchJson<LiveArticleDto>(`/api/v1/admin/articles/${id}`, {
      method: "PATCH",
      body: JSON.stringify(toArticlePayload(payload)),
    }).then(toAdminArticle),
  deleteArticle: (id: string) =>
    fetchJson<void>(`/api/v1/admin/articles/${id}`, { method: "DELETE" }),
  transition: (id: string, action: LifecycleAction) =>
    fetchJson<LiveArticleDto>(`/api/v1/admin/articles/${id}/lifecycle`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }).then(toAdminArticle),
};

// -------------------------------------------------- live affiliate client
async function affiliateFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${AFFILIATE_API_BASE}${path}`, {
    ...init,
    headers: {
      ...liveHeaders(),
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`Affiliate API request failed: ${response.status} ${response.statusText}`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

interface LiveNetworkDto {
  id: string;
  code: string;
  name: string;
  status: string;
  feed_type: string;
  webhook_secret_ref: string;
  settings_json: string;
  created_at: string;
  updated_at: string;
}

interface LiveMerchantDto {
  id: string;
  network_id: string;
  remote_merchant_id: string;
  name: string;
  status: string;
  commission_terms_json: string;
}

interface LiveProductDto {
  id: string;
  niche_id: string;
  merchant_id: string;
  sku: string;
  slug: string;
  name: string;
  excerpt: string;
  price_cents: number;
  currency: string;
  status: string;
  checksum: string | null;
  last_feed_at: string | null;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

interface LiveCategoryDto {
  id: string;
  niche_id: string;
  parent_id: string | null;
  name: string;
  slug: string;
  path: string | null;
  sort_order: number;
  status: string;
}

interface LiveLinkDto {
  id: string;
  niche_id: string;
  product_id: string;
  network_id: string;
  network_link_url: string;
  default_commission_rate: string;
  status: string;
  disclosure_required: boolean;
  created_at: string;
  updated_at: string;
}

interface LiveClickDto {
  id: string;
  niche_id: string;
  link_token_id: string;
  attribution_id: string | null;
  revenue_transaction_id: string | null;
  clicked_at: string;
  ip_hash: string | null;
  user_agent_hash: string | null;
  referrer: string | null;
  is_bot: boolean;
  fraud_flag: boolean;
}

interface LiveRevenueDto {
  id: string;
  niche_id: string;
  network_id: string;
  affiliate_link_id: string;
  affiliate_click_id: string | null;
  network_transaction_id: string;
  gross_cents: number;
  commission_cents: number;
  currency: string;
  status: string;
  occurred_at: string;
  reconciled_at: string | null;
  created_at: string;
}

interface LiveReconciliationDto {
  id: string;
  niche_id: string;
  network_id: string;
  reported_at: string;
  expected_total_cents: number;
  actual_total_cents: number;
  delta_cents: number;
  status: string;
  report_ref: string | null;
  created_at: string;
}

interface LiveSummaryDto {
  id: string;
  niche_id: string;
  network_id: string | null;
  summary_date: string;
  clicks: number;
  sales: number;
  gross_cents: number;
  commission_cents: number;
  currency: string;
}

interface LiveDashboardDto {
  total_commission_cents: number;
  approved_commission_cents: number;
  pending_commission_cents: number;
  paid_commission_cents: number;
  transaction_count: number;
  click_count: number;
}

function toNetwork(dto: LiveNetworkDto): AdminNetwork {
  return {
    id: dto.id,
    code: dto.code,
    name: dto.name,
    status: dto.status,
    feedType: dto.feed_type,
    webhookSecretRef: dto.webhook_secret_ref,
    settingsJson: dto.settings_json,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

function toMerchant(dto: LiveMerchantDto): AdminMerchant {
  return {
    id: dto.id,
    networkId: dto.network_id,
    remoteMerchantId: dto.remote_merchant_id,
    name: dto.name,
    status: dto.status,
    commissionTermsJson: dto.commission_terms_json,
  };
}

function toProduct(dto: LiveProductDto): AdminProduct {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    merchantId: dto.merchant_id,
    sku: dto.sku,
    slug: dto.slug,
    name: dto.name,
    excerpt: dto.excerpt,
    priceCents: dto.price_cents,
    currency: dto.currency,
    status: dto.status,
    checksum: dto.checksum,
    lastFeedAt: dto.last_feed_at,
    deletedAt: dto.deleted_at,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

function toCategory(dto: LiveCategoryDto): AdminProductCategory {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    parentId: dto.parent_id,
    name: dto.name,
    slug: dto.slug,
    path: dto.path,
    sortOrder: dto.sort_order,
    status: dto.status,
  };
}

function toLink(dto: LiveLinkDto): AdminAffiliateLink {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    productId: dto.product_id,
    networkId: dto.network_id,
    networkLinkUrl: dto.network_link_url,
    defaultCommissionRate: dto.default_commission_rate,
    status: dto.status,
    disclosureRequired: dto.disclosure_required,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

function toClick(dto: LiveClickDto): AdminClick {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    linkTokenId: dto.link_token_id,
    attributionId: dto.attribution_id,
    revenueTransactionId: dto.revenue_transaction_id,
    clickedAt: dto.clicked_at,
    ipHash: dto.ip_hash,
    userAgentHash: dto.user_agent_hash,
    referrer: dto.referrer,
    isBot: dto.is_bot,
    fraudFlag: dto.fraud_flag,
  };
}

function toRevenue(dto: LiveRevenueDto): AdminRevenueTransaction {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    networkId: dto.network_id,
    affiliateLinkId: dto.affiliate_link_id,
    affiliateClickId: dto.affiliate_click_id,
    networkTransactionId: dto.network_transaction_id,
    grossCents: dto.gross_cents,
    commissionCents: dto.commission_cents,
    currency: dto.currency,
    status: dto.status,
    occurredAt: dto.occurred_at,
    reconciledAt: dto.reconciled_at,
    createdAt: dto.created_at,
  };
}

function toReconciliation(dto: LiveReconciliationDto): AdminReconciliation {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    networkId: dto.network_id,
    reportedAt: dto.reported_at,
    expectedTotalCents: dto.expected_total_cents,
    actualTotalCents: dto.actual_total_cents,
    deltaCents: dto.delta_cents,
    status: dto.status,
    reportRef: dto.report_ref,
    createdAt: dto.created_at,
  };
}

function toSummary(dto: LiveSummaryDto): AdminRevenueSummary {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    networkId: dto.network_id,
    summaryDate: dto.summary_date,
    clicks: dto.clicks,
    sales: dto.sales,
    grossCents: dto.gross_cents,
    commissionCents: dto.commission_cents,
    currency: dto.currency,
  };
}

const liveAffiliateClient = {
  listNetworks: () =>
    affiliateFetchJson<LiveNetworkDto[]>("/api/v1/admin/networks").then((items) =>
      items.map(toNetwork),
    ),
  createNetwork: (payload: AdminNetworkCreate) =>
    affiliateFetchJson<LiveNetworkDto>("/api/v1/admin/networks", {
      method: "POST",
      body: JSON.stringify(payload),
    }).then(toNetwork),
  listMerchants: () =>
    affiliateFetchJson<LiveMerchantDto[]>("/api/v1/admin/merchants").then((items) =>
      items.map(toMerchant),
    ),
  listCategories: () =>
    affiliateFetchJson<LiveCategoryDto[]>("/api/v1/admin/product-categories").then((items) =>
      items.map(toCategory),
    ),
  listProducts: () => {
    const query = new URLSearchParams({ page_size: "100" });
    return affiliateFetchJson<LivePageDto<LiveProductDto>>(
      `/api/v1/admin/products?${query.toString()}`,
    ).then((page) => page.items.map(toProduct));
  },
  listLinks: () => {
    const query = new URLSearchParams({ page_size: "100" });
    return affiliateFetchJson<LivePageDto<LiveLinkDto>>(
      `/api/v1/admin/links?${query.toString()}`,
    ).then((page) => page.items.map(toLink));
  },
  listClicks: () => {
    const query = new URLSearchParams({ page_size: "100" });
    return affiliateFetchJson<LivePageDto<LiveClickDto>>(
      `/api/v1/admin/clicks?${query.toString()}`,
    ).then((page) => page.items.map(toClick));
  },
  listRevenue: (status?: string) => {
    const query = new URLSearchParams({ page_size: "100" });
    if (status) query.set("status", status);
    return affiliateFetchJson<LivePageDto<LiveRevenueDto>>(
      `/api/v1/admin/revenue?${query.toString()}`,
    ).then((page) => page.items.map(toRevenue));
  },
  transitionCommission: (id: string, action: "approve" | "reject" | "mark_paid") =>
    affiliateFetchJson<LiveRevenueDto>(`/api/v1/admin/revenue/${id}/transition`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }).then(toRevenue),
  listReconciliations: () => {
    const query = new URLSearchParams({ page_size: "100" });
    return affiliateFetchJson<LivePageDto<LiveReconciliationDto>>(
      `/api/v1/admin/reconciliations?${query.toString()}`,
    ).then((page) => page.items.map(toReconciliation));
  },
  listSummaries: () => {
    const query = new URLSearchParams({ page_size: "100" });
    return affiliateFetchJson<LivePageDto<LiveSummaryDto>>(
      `/api/v1/admin/revenue-summaries?${query.toString()}`,
    ).then((page) => page.items.map(toSummary));
  },
  revenueDashboard: () =>
    affiliateFetchJson<LiveDashboardDto>("/api/v1/admin/revenue/dashboard").then((dto) => ({
      totalCommissionCents: dto.total_commission_cents,
      approvedCommissionCents: dto.approved_commission_cents,
      pendingCommissionCents: dto.pending_commission_cents,
      paidCommissionCents: dto.paid_commission_cents,
      transactionCount: dto.transaction_count,
      clickCount: dto.click_count,
    })),
};

const liveAdminApiClient: AdminApiClient = {
  dashboard: mockAdminApiClient.dashboard,
  analytics: mockAdminApiClient.analytics,
  pinterest: mockAdminApiClient.pinterest,
  automation: mockAdminApiClient.automation,
  content: liveContentClient,
  affiliate: liveAffiliateClient,
};

export function createAdminApiClient(): AdminApiClient {
  return CONTENT_API_BASE || AFFILIATE_API_BASE ? liveAdminApiClient : mockAdminApiClient;
}

export { PAGE_TITLES };
