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
  OPS_OVERVIEW,
  SYSTEM_STATUS,
  ISOLATION_CHECK,
  AUDIT_LOGS,
  QUEUE_ITEMS,
  WEBHOOK_LOGS,
  OPERATION_LOGS,
  SCHEDULED_JOBS,
  JOB_RUNS,
  OPS_NOTIFICATIONS,
  MOCK_AUTOMATION_EXECUTORS,
  MOCK_AUTOMATION_JOBS,
  MOCK_AUTOMATION_QUEUE,
  MOCK_AUTOMATION_RUNS,
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

// ---------------------------------------------------- automation read models
export interface AdminAutomationRule {
  id: string;
  nicheId: string | null;
  code: string;
  triggerType: string;
  status: string;
  runAsUserId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface AdminScheduledJob {
  id: string;
  nicheId: string | null;
  jobKey: string;
  cronExpr: string;
  queue: string;
  handler: string;
  status: string;
  lastRunAt: string | null;
  nextRunAt: string | null;
}

export interface AdminJobRunDetail {
  id: string;
  nicheId: string | null;
  nicheSlug: string | null;
  scheduledJobId: string;
  jobKey: string;
  runAt: string;
  status: string;
  attempts: number;
  startedAt: string | null;
  finishedAt: string | null;
  outputRef: string | null;
  error: string | null;
}

export interface AdminQueueItemDetail {
  id: string;
  nicheId: string | null;
  nicheSlug: string | null;
  queue: string;
  payloadRef: string;
  state: string;
  attempts: number;
  maxAttempts: number;
  runAt: string;
  completedAt: string | null;
  error: string | null;
}

export interface AdminExecutor {
  id: string;
  name: string;
  queue: string;
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
    getOverview(from: string, to: string, accountId?: string): Promise<AnalyticsOverview>;
    getTrafficSeries(from: string, to: string, source?: string, accountId?: string): Promise<AnalyticsTrafficPoint[]>;
    getTrafficSources(from: string, to: string): Promise<AnalyticsTrafficSource[]>;
    getTopPages(from: string, to: string, limit?: number): Promise<AnalyticsTopPage[]>;
    getMetricSeries(from: string, to: string, metricKey?: string, accountId?: string): Promise<AnalyticsMetricPoint[]>;
    getEvents(from: string, to: string, eventType?: string, accountId?: string, limit?: number): Promise<AnalyticsLedgerEvent[]>;
    getKpis(from: string, to: string, kind?: string, limit?: number): Promise<AnalyticsKpiSnapshot[]>;
    getPipeline(): Promise<AnalyticsPipelineStatus>;
    runRollups(from: string, to: string): Promise<{ nicheId: string; rollupDate: string; trafficRows: number }[]>;
  };
  pinterest: {
    getAccounts(): Promise<typeof PIN_ACCOUNTS>;
    getPinQueue(): Promise<typeof PIN_QUEUE>;
  };
  automation: {
    getRules(): Promise<AdminAutomationRule[]>;
    enableRule(id: string): Promise<AdminAutomationRule>;
    disableRule(id: string): Promise<AdminAutomationRule>;
    getJobs(): Promise<AdminScheduledJob[]>;
    runJob(id: string, config?: Record<string, unknown>): Promise<{ run: AdminJobRunDetail; queueItem: AdminQueueItemDetail }>;
    getJobRuns(status?: string): Promise<AdminJobRunDetail[]>;
    retryRun(id: string): Promise<{ run: AdminJobRunDetail; queueItem: AdminQueueItemDetail }>;
    cancelRun(id: string): Promise<AdminJobRunDetail>;
    getQueue(state?: string): Promise<AdminQueueItemDetail[]>;
    retryQueueItem(id: string): Promise<AdminQueueItemDetail>;
    cancelQueueItem(id: string): Promise<AdminQueueItemDetail>;
    getExecutors(): Promise<AdminExecutor[]>;
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
  ops: {
    getOverview(): Promise<OpsOverview>;
    getSystemStatus(): Promise<SystemStatus>;
    getIsolationCheck(): Promise<IsolationCheck>;
    getAudit(filters?: AuditFilters): Promise<AuditEntry[]>;
    getQueue(filters?: QueueFilters): Promise<OpsQueueItem[]>;
    retryQueueItem(id: string): Promise<OpsQueueItem>;
    getWebhookLogs(filters?: LogFilters): Promise<WebhookLogEntry[]>;
    getOperationLogs(filters?: LogFilters): Promise<OperationLogEntry[]>;
    getJobs(): Promise<ScheduledJobEntry[]>;
    getJobRuns(status?: string): Promise<JobRunEntry[]>;
    getNotifications(): Promise<NotificationEntry[]>;
    markNotificationRead(id: string): Promise<NotificationEntry>;
  };
}


// --------------------------------------------------------- ops read models
export interface OpsOverview {
  failedQueueItems: number;
  failedWebhooks: number;
  failedOperations: number;
  failedJobRuns: number;
  openNotifications: number;
  auditEntries: number;
  queues: Record<string, number>;
}

export interface ServiceStatus {
  id: string;
  name: string;
  status: "ok" | "degraded" | "down" | "unknown";
  version: string | null;
  latencyMs: number | null;
  error: string | null;
}

export interface SystemStatus {
  overall: string;
  services: ServiceStatus[];
}

export interface IsolationCheck {
  ok: boolean;
  checks: { table: string; rows: number; orphaned: string[] }[];
}

export interface AuditFilters {
  action?: string;
  entityType?: string;
  entityId?: string;
  requestId?: string;
  nicheId?: string;
  limit?: number;
  offset?: number;
}

export interface AuditEntry {
  id: string;
  nicheId: string | null;
  adminUserId: string | null;
  apiKeyId: string | null;
  action: string;
  entityType: string;
  entityId: string;
  beforeJson: string | null;
  afterJson: string | null;
  requestId: string | null;
  occurredAt: string;
}

export interface QueueFilters {
  queue?: string;
  state?: string;
  limit?: number;
}

export interface OpsQueueItem {
  id: string;
  nicheId: string | null;
  queue: string;
  payloadRef: string;
  state: string;
  attempts: number;
  maxAttempts: number;
  runAt: string;
  error: string | null;
}

export interface LogFilters {
  source?: string;
  status?: string;
  operation?: string;
  nicheId?: string;
  limit?: number;
}

export interface WebhookLogEntry {
  id: string;
  nicheId: string | null;
  source: string;
  eventId: string;
  status: string;
  receivedAt: string;
  error: string | null;
}

export interface OperationLogEntry {
  id: string;
  nicheId: string | null;
  operation: string;
  entityType: string;
  entityId: string;
  status: string;
  message: string;
  occurredAt: string;
}

export interface ScheduledJobEntry {
  id: string;
  nicheId: string | null;
  jobKey: string;
  cronExpr: string;
  queue: string;
  handler: string;
  status: string;
  nextRunAt: string | null;
}

export interface JobRunEntry {
  id: string;
  scheduledJobId: string;
  status: string;
  attempts: number;
  runAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  error: string | null;
}

export interface NotificationEntry {
  id: string;
  nicheId: string | null;
  recipientId: string;
  type: string;
  title: string;
  body: string;
  status: string;
  createdAt: string;
  readAt: string | null;
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

// ------------------------------------------------------------- analytics (M8)
export interface AnalyticsOverview {
  sessions: number;
  pageviews: number;
  uniqueVisitors: number;
  bounceRate: number;
  affiliateClicks: number;
  conversions: number;
  revenueAmount: number;
  pinClicks: number;
}

export interface AnalyticsTrafficPoint {
  label: string;
  pinterest: number;
  organic: number;
  direct: number;
  other: number;
}

export interface AnalyticsTrafficSource {
  name: string;
  value: number;
  color: string;
}

export interface AnalyticsTopPage {
  id: string;
  path: string;
  visits: number;
  uniqueVisitors: number;
  conversion: string;
}

export interface AnalyticsMetricPoint {
  date: string;
  metricKey: string;
  value: number;
  units: string;
  pinterestAccountId: string | null;
}

export interface AnalyticsLedgerEvent {
  id: string;
  eventId: string;
  eventType: string;
  source: string;
  sessionId: string | null;
  pageUrl: string | null;
  pinterestAccountId: string | null;
  occurredAt: string;
  receivedAt: string;
}

export interface AnalyticsKpiSnapshot {
  id: string;
  nicheId: string;
  snapshotDate: string;
  snapshotKind: string;
  payloadJson: string;
  createdAt: string;
}

export interface AnalyticsPipelineStatus {
  backbone: string;
  warehouse: string;
  [key: string]: string | number | boolean;
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


const mockAnalyticsClient = {
  getOverview: (_from: string, _to: string) =>
    delay({
      sessions: 128430,
      pageviews: 386400,
      uniqueVisitors: 93410,
      bounceRate: 0.412,
      affiliateClicks: 34800,
      conversions: 1152,
      revenueAmount: 4128.5,
      pinClicks: 51220,
    }),
  getTrafficSeries: (_from: string, _to: string) =>
    delay(
      TRAFFIC_SERIES.map((row) => ({
        label: row.label,
        pinterest: row.pinterest,
        organic: row.organic,
        direct: row.direct,
        other: 0,
      })),
    ),
  getTrafficSources: (_from: string, _to: string) => delay(TRAFFIC_SOURCES),
  getTopPages: (_from: string, _to: string, limit = 20) =>
    delay(
      TOP_PAGES.slice(0, limit).map((page) => ({
        id: page.id,
        path: page.path,
        visits: page.visits,
        uniqueVisitors: Math.round(page.visits * 0.72),
        conversion: page.conversion,
      })),
    ),
  getMetricSeries: (from: string, to: string, _metricKey?: string) => {
    const start = new Date(`${from}T00:00:00Z`);
    const end = new Date(`${to}T00:00:00Z`);
    const points: AnalyticsMetricPoint[] = [];
    const clicks = [34800, 35100, 35750, 36200, 36900, 37400];
    const conversions = [1152, 1180, 1210, 1235, 1280, 1310];
    const revenue = [4128.5, 4230.0, 4310.75, 4420.2, 4550.9, 4680.4];
    let index = 0;
    for (let date = new Date(start); date <= end; date.setUTCDate(date.getUTCDate() + 7)) {
      const iso = date.toISOString().slice(0, 10);
      points.push({ date: iso, metricKey: "affiliate.clicks", value: clicks[index % clicks.length], units: "count", pinterestAccountId: null });
      points.push({ date: iso, metricKey: "conversions", value: conversions[index % conversions.length], units: "count", pinterestAccountId: null });
      points.push({ date: iso, metricKey: "revenue.amount", value: revenue[index % revenue.length], units: "usd", pinterestAccountId: null });
      index += 1;
    }
    return delay(points);
  },
  getEvents: (_from: string, _to: string, _eventType?: string, _accountId?: string, _limit = 100) =>
    delay([] as AnalyticsLedgerEvent[]),
  getKpis: (_from: string, _to: string, _kind?: string, _limit = 100) =>
    delay([] as AnalyticsKpiSnapshot[]),
  getPipeline: () =>
    delay({ backbone: "in-memory", warehouse: "in-memory", kafkaEnabled: false, clickhouseEnabled: false } as AnalyticsPipelineStatus),
  runRollups: (_from: string, _to: string) => delay([]),
};

const mockAdminApiClient: AdminApiClient = {
  dashboard: {
    getKpis: () => delay(DASHBOARD_KPIS),
    getRevenueSeries: () => delay(REVENUE_SERIES),
    getTrafficSeries: () => delay(TRAFFIC_SERIES),
    getTopPages: () => delay(TOP_PAGES),
    getNotifications: () => delay(NOTIFICATIONS),
  },
  analytics: mockAnalyticsClient,
  pinterest: {
    getAccounts: () => delay(PIN_ACCOUNTS),
    getPinQueue: () => delay(PIN_QUEUE),
  },
  automation: {
    getRules: () => delay(AUTOMATION_RULES),
    enableRule: (id: string) => {
      const rule = AUTOMATION_RULES.find((r) => r.id === id);
      if (!rule) return Promise.reject(new Error("Rule not found"));
      return delay({ ...rule, status: "enabled" });
    },
    disableRule: (id: string) => {
      const rule = AUTOMATION_RULES.find((r) => r.id === id);
      if (!rule) return Promise.reject(new Error("Rule not found"));
      return delay({ ...rule, status: "disabled" });
    },
    getJobs: () => delay(MOCK_AUTOMATION_JOBS),
    runJob: (id: string, _config?: Record<string, unknown>) => {
      const job = MOCK_AUTOMATION_JOBS.find((j) => j.id === id);
      if (!job) return Promise.reject(new Error("Job not found"));
      return delay({
        run: {
          id: `run-${Date.now()}`,
          nicheId: job.nicheId,
          nicheSlug: null,
          scheduledJobId: job.id,
          jobKey: job.jobKey,
          runAt: new Date().toISOString(),
          status: "pending",
          attempts: 0,
          startedAt: null,
          finishedAt: null,
          outputRef: null,
          error: null,
        },
        queueItem: {
          id: `q-${Date.now()}`,
          nicheId: job.nicheId,
          nicheSlug: null,
          queue: job.queue,
          payloadRef: "job_run:new",
          state: "queued",
          attempts: 0,
          maxAttempts: 5,
          runAt: new Date().toISOString(),
          completedAt: null,
          error: null,
        },
      });
    },
    getJobRuns: (status?: string) => {
      const rows = status ? MOCK_AUTOMATION_RUNS.filter((run) => run.status === status) : MOCK_AUTOMATION_RUNS;
      return delay(rows);
    },
    retryRun: (id: string) => {
      const run = MOCK_AUTOMATION_RUNS.find((r) => r.id === id);
      if (!run) return Promise.reject(new Error("Run not found"));
      const job = MOCK_AUTOMATION_JOBS.find((j) => j.id === run.scheduledJobId);
      return delay({
        run: { ...run, id: `run-${Date.now()}`, status: "pending", attempts: 0, startedAt: null, finishedAt: null, error: null },
        queueItem: {
          id: `q-${Date.now()}`,
          nicheId: run.nicheId,
          nicheSlug: run.nicheSlug,
          queue: job?.queue ?? "default",
          payloadRef: "job_run:new",
          state: "queued",
          attempts: 0,
          maxAttempts: 5,
          runAt: new Date().toISOString(),
          completedAt: null,
          error: null,
        },
      });
    },
    cancelRun: (id: string) => {
      const run = MOCK_AUTOMATION_RUNS.find((r) => r.id === id);
      if (!run) return Promise.reject(new Error("Run not found"));
      return delay({ ...run, status: "cancelled", finishedAt: new Date().toISOString() });
    },
    getQueue: (state?: string) => {
      const rows = state ? MOCK_AUTOMATION_QUEUE.filter((item) => item.state === state) : MOCK_AUTOMATION_QUEUE;
      return delay(rows);
    },
    retryQueueItem: (id: string) => {
      const item = MOCK_AUTOMATION_QUEUE.find((entry) => entry.id === id);
      if (!item) return Promise.reject(new Error("Queue item not found"));
      return delay({ ...item, state: "queued", completedAt: null, error: null });
    },
    cancelQueueItem: (id: string) => {
      const item = MOCK_AUTOMATION_QUEUE.find((entry) => entry.id === id);
      if (!item) return Promise.reject(new Error("Queue item not found"));
      return delay({ ...item, state: "failed", completedAt: new Date().toISOString(), error: "cancelled by operator" });
    },
    getExecutors: () => delay(MOCK_AUTOMATION_EXECUTORS),
  },
  content: mockContentClient,
  affiliate: mockAffiliateClient,
  ops: {
    getOverview: () => delay(OPS_OVERVIEW),
    getSystemStatus: () => delay(SYSTEM_STATUS),
    getIsolationCheck: () => delay(ISOLATION_CHECK),
    getAudit: (filters?: AuditFilters) => {
      let rows = AUDIT_LOGS;
      if (filters?.action) rows = rows.filter((row) => row.action === filters.action);
      if (filters?.entityType) rows = rows.filter((row) => row.entityType === filters.entityType);
      if (filters?.limit) rows = rows.slice(0, filters.limit);
      return delay(rows);
    },
    getQueue: (filters?: QueueFilters) => {
      let rows = QUEUE_ITEMS;
      if (filters?.state) rows = rows.filter((item) => item.state === filters.state);
      if (filters?.queue) rows = rows.filter((item) => item.queue === filters.queue);
      return delay(rows);
    },
    retryQueueItem: (id: string) => {
      const item = QUEUE_ITEMS.find((entry) => entry.id === id);
      if (!item) return Promise.reject(new Error("Queue item not found"));
      return delay({ ...item, state: "queued", error: null });
    },
    getWebhookLogs: (filters?: LogFilters) => {
      let rows = WEBHOOK_LOGS;
      if (filters?.source) rows = rows.filter((entry) => entry.source === filters.source);
      if (filters?.status) rows = rows.filter((entry) => entry.status === filters.status);
      return delay(rows);
    },
    getOperationLogs: (filters?: LogFilters) => {
      let rows = OPERATION_LOGS;
      if (filters?.operation) rows = rows.filter((entry) => entry.operation === filters.operation);
      if (filters?.status) rows = rows.filter((entry) => entry.status === filters.status);
      return delay(rows);
    },
    getJobs: () => delay(SCHEDULED_JOBS),
    getJobRuns: (status?: string) => {
      const rows = status ? JOB_RUNS.filter((run) => run.status === status) : JOB_RUNS;
      return delay(rows);
    },
    getNotifications: () => delay(OPS_NOTIFICATIONS),
    markNotificationRead: (id: string) => {
      const entry = OPS_NOTIFICATIONS.find((item) => item.id === id);
      if (!entry) return Promise.reject(new Error("Notification not found"));
      return delay({ ...entry, status: "read", readAt: new Date().toISOString() });
    },
  },
};

// ------------------------------------------------------------------ live mode
const CONTENT_API_BASE = process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL ?? "";
const AFFILIATE_API_BASE = process.env.NEXT_PUBLIC_AFFILIATE_API_BASE_URL ?? "";
const ANALYTICS_API_BASE = process.env.NEXT_PUBLIC_ANALYTICS_API_BASE_URL ?? "";
const ADMIN_API_BASE = process.env.NEXT_PUBLIC_ADMIN_API_BASE_URL ?? "";

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

function analyticsFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  return fetch(`${ANALYTICS_API_BASE}${path}`, {
    ...init,
    headers: { ...liveHeaders(), ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`Admin analytics API request failed: ${response.status} ${response.statusText}`);
    }
    return (await response.json()) as T;
  });
}

function analyticsDateRange(from: string, to: string, extra?: Record<string, string>) {
  const query = new URLSearchParams({ from_date: from, to_date: to });
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      if (value) query.set(key, value);
    }
  }
  return `?${query.toString()}`;
}

/** Bucket daily traffic rows into weekly points compatible with the chart. */
function toTrafficSeries(points: LiveAnalyticsTrafficDto["points"]): AnalyticsTrafficPoint[] {
  const buckets = new Map<string, AnalyticsTrafficPoint>();
  for (const point of points) {
    const date = new Date(`${point.date}T00:00:00Z`);
    const day = (date.getUTCDay() + 6) % 7; // Monday = 0
    const weekStart = new Date(date);
    weekStart.setUTCDate(date.getUTCDate() - day);
    const key = weekStart.toISOString().slice(0, 10);
    const label = `${weekStart.getUTCMonth() + 1}/${weekStart.getUTCDate()}`;
    let bucket = buckets.get(key);
    if (!bucket) {
      bucket = { label, pinterest: 0, organic: 0, direct: 0, other: 0 };
      buckets.set(key, bucket);
    }
    if (point.source === "pinterest") bucket.pinterest += point.sessions;
    else if (point.source === "google" || point.source === "email") bucket.organic += point.sessions;
    else if (point.source === "direct") bucket.direct += point.sessions;
    else bucket.other += point.sessions;
  }
  return [...buckets.values()];
}

const SOURCE_COLORS: Record<string, string> = {
  Pinterest: "var(--color-danger-500)",
  "Organic search": "var(--color-primary-500)",
  Direct: "var(--color-success-500)",
  Other: "var(--color-text-400)",
};

function toTrafficSources(points: LiveAnalyticsTrafficDto["points"]): AnalyticsTrafficSource[] {
  const totals = new Map<string, number>();
  let sum = 0;
  for (const point of points) {
    totals.set(point.source, (totals.get(point.source) ?? 0) + point.sessions);
    sum += point.sessions;
  }
  if (sum === 0) return [];
  const names: Record<string, string> = {
    pinterest: "Pinterest",
    google: "Organic search",
    direct: "Direct",
    email: "Email",
    other: "Other",
  };
  return [...totals.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([source, sessions]) => {
      const name = names[source] ?? "Other";
      return { name, value: Math.round((sessions / sum) * 100), color: SOURCE_COLORS[name] ?? SOURCE_COLORS.Other };
    });
}

const liveAnalyticsClient = {
  getOverview: (from: string, to: string, accountId?: string) =>
    analyticsFetchJson<LiveAnalyticsOverviewDto>(
      `/api/v1/admin/overview${analyticsDateRange(from, to, accountId ? { account_id: accountId } : undefined)}`,
    ).then((dto) => ({
      sessions: dto.sessions,
      pageviews: dto.pageviews,
      uniqueVisitors: dto.unique_visitors,
      bounceRate: dto.bounce_rate,
      affiliateClicks: dto.affiliate_clicks,
      conversions: dto.conversions,
      revenueAmount: dto.revenue_amount,
      pinClicks: dto.pin_clicks,
    })),
  getTrafficSeries: (from: string, to: string, source?: string, accountId?: string) =>
    analyticsFetchJson<LiveAnalyticsTrafficDto>(
      `/api/v1/admin/traffic${analyticsDateRange(from, to, {
        ...(source ? { source } : {}),
        ...(accountId ? { account_id: accountId } : {}),
      })}`,
    ).then((dto) => toTrafficSeries(dto.points)),
  getTrafficSources: (from: string, to: string) =>
    analyticsFetchJson<LiveAnalyticsTrafficDto>(
      `/api/v1/admin/traffic${analyticsDateRange(from, to)}`,
    ).then((dto) => toTrafficSources(dto.points)),
  getTopPages: (from: string, to: string, limit = 20) =>
    analyticsFetchJson<LiveAnalyticsTopPagesDto>(
      `/api/v1/admin/top-pages${analyticsDateRange(from, to, { limit: String(limit) })}`,
    ).then((dto) =>
      dto.rows.map((row) => ({
        id: row.page_url,
        path: row.page_url,
        visits: row.pageviews,
        uniqueVisitors: row.unique_visitors,
        conversion: row.unique_visitors > 0 ? `${(row.pageviews / row.unique_visitors).toFixed(2)}x` : "\u2014",
      })),
    ),
  getMetricSeries: (from: string, to: string, metricKey?: string, accountId?: string) =>
    analyticsFetchJson<LiveAnalyticsMetricDto>(
      `/api/v1/admin/metrics${analyticsDateRange(from, to, {
        ...(metricKey ? { metric_key: metricKey } : {}),
        ...(accountId ? { account_id: accountId } : {}),
      })}`,
    ).then((dto) =>
      dto.points.map((point) => ({
        date: point.date,
        metricKey: point.metric_key,
        value: point.value,
        units: point.units,
        pinterestAccountId: point.pinterest_account_id,
      })),
    ),
  getEvents: (from: string, to: string, eventType?: string, accountId?: string, limit = 100) => {
    const query = new URLSearchParams({ start: `${from}T00:00:00Z`, end: `${to}T23:59:59Z` });
    if (eventType) query.set("event_type", eventType);
    if (accountId) query.set("account_id", accountId);
    query.set("limit", String(limit));
    return analyticsFetchJson<LiveAnalyticsLedgerEventDto[]>(`/api/v1/admin/events?${query.toString()}`).then(
      (items) =>
        items.map((item) => ({
          id: item.id,
          eventId: item.event_id,
          eventType: item.event_type,
          source: item.source,
          sessionId: item.session_id,
          pageUrl: item.page_url,
          pinterestAccountId: item.pinterest_account_id,
          occurredAt: item.occurred_at,
          receivedAt: item.received_at,
        })),
    );
  },
  getKpis: (from: string, to: string, kind?: string, limit = 100) => {
    const query = new URLSearchParams({ start: from, end: to });
    if (kind) query.set("snapshot_kind", kind);
    query.set("limit", String(limit));
    return analyticsFetchJson<LiveAnalyticsKpiSnapshotDto[]>(`/api/v1/admin/kpis?${query.toString()}`).then(
      (items) =>
        items.map((item) => ({
          id: item.id,
          nicheId: item.niche_id,
          snapshotDate: item.snapshot_date,
          snapshotKind: item.snapshot_kind,
          payloadJson: item.payload_json,
          createdAt: item.created_at,
        })),
    );
  },
  getPipeline: () => analyticsFetchJson<AnalyticsPipelineStatus>("/api/v1/admin/pipeline"),
  runRollups: (from: string, to: string) =>
    analyticsFetchJson<{ niche_id: string; rollup_date: string; traffic_rows: number }[]>(
      `/api/v1/admin/rollups${analyticsDateRange(from, to)}`,
      { method: "POST" },
    ).then((items) =>
      items.map((item) => ({
        nicheId: item.niche_id,
        rollupDate: item.rollup_date,
        trafficRows: item.traffic_rows,
      })),
    ),
};

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

interface LiveAnalyticsOverviewDto {
  sessions: number;
  pageviews: number;
  unique_visitors: number;
  bounce_rate: number;
  affiliate_clicks: number;
  conversions: number;
  revenue_amount: number;
  pin_clicks: number;
}

interface LiveAnalyticsTrafficDto {
  points: {
    date: string;
    source: string;
    sessions: number;
    pageviews: number;
    unique_visitors: number;
    bounce_rate: number;
  }[];
}

interface LiveAnalyticsTopPagesDto {
  rows: {
    page_url: string;
    pageviews: number;
    unique_visitors: number;
    last_seen: string | null;
  }[];
}

interface LiveAnalyticsMetricDto {
  points: {
    date: string;
    metric_key: string;
    value: number;
    units: string;
    pinterest_account_id: string | null;
  }[];
}

interface LiveAnalyticsLedgerEventDto {
  id: string;
  event_id: string;
  event_type: string;
  source: string;
  session_id: string | null;
  page_url: string | null;
  pinterest_account_id: string | null;
  occurred_at: string;
  received_at: string;
}

interface LiveAnalyticsKpiSnapshotDto {
  id: string;
  niche_id: string;
  snapshot_date: string;
  snapshot_kind: string;
  payload_json: string;
  created_at: string;
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

// ------------------------------------------------------- live ops client
function adminFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  return fetch(`${ADMIN_API_BASE}${path}`, {
    ...init,
    headers: { ...liveHeaders(), ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`Admin ops API request failed: ${response.status} ${response.statusText}`);
    }
    return (await response.json()) as T;
  });
}

interface LiveAuditDto {
  id: string;
  niche_id: string | null;
  admin_user_id: string | null;
  api_key_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  before_json: string | null;
  after_json: string | null;
  request_id: string | null;
  occurred_at: string;
}

interface LiveQueueDto {
  id: string;
  niche_id: string | null;
  queue: string;
  payload_ref: string;
  state: string;
  attempts: number;
  max_attempts: number;
  run_at: string;
  error: string | null;
}

interface LiveWebhookDto {
  id: string;
  niche_id: string | null;
  source: string;
  event_id: string;
  status: string;
  received_at: string;
  error: string | null;
}

interface LiveOperationDto {
  id: string;
  niche_id: string | null;
  operation: string;
  entity_type: string;
  entity_id: string;
  status: string;
  message: string;
  occurred_at: string;
}

interface LiveJobDto {
  id: string;
  niche_id: string | null;
  job_key: string;
  cron_expr: string;
  queue: string;
  handler: string;
  status: string;
  next_run_at: string | null;
}

interface LiveJobRunDto {
  id: string;
  scheduled_job_id: string;
  status: string;
  attempts: number;
  run_at: string;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
}

interface LiveNotificationDto {
  id: string;
  niche_id: string | null;
  recipient_id: string;
  type: string;
  title: string;
  body: string;
  status: string;
  created_at: string;
  read_at: string | null;
}

function toAuditEntry(dto: LiveAuditDto): AuditEntry {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    adminUserId: dto.admin_user_id,
    apiKeyId: dto.api_key_id,
    action: dto.action,
    entityType: dto.entity_type,
    entityId: dto.entity_id,
    beforeJson: dto.before_json,
    afterJson: dto.after_json,
    requestId: dto.request_id,
    occurredAt: dto.occurred_at,
  };
}

function toQueueItem(dto: LiveQueueDto): OpsQueueItem {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    queue: dto.queue,
    payloadRef: dto.payload_ref,
    state: dto.state,
    attempts: dto.attempts,
    maxAttempts: dto.max_attempts,
    runAt: dto.run_at,
    error: dto.error,
  };
}

function toWebhookEntry(dto: LiveWebhookDto): WebhookLogEntry {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    source: dto.source,
    eventId: dto.event_id,
    status: dto.status,
    receivedAt: dto.received_at,
    error: dto.error,
  };
}

function toOperationEntry(dto: LiveOperationDto): OperationLogEntry {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    operation: dto.operation,
    entityType: dto.entity_type,
    entityId: dto.entity_id,
    status: dto.status,
    message: dto.message,
    occurredAt: dto.occurred_at,
  };
}

function toScheduledJob(dto: LiveJobDto): ScheduledJobEntry {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    jobKey: dto.job_key,
    cronExpr: dto.cron_expr,
    queue: dto.queue,
    handler: dto.handler,
    status: dto.status,
    nextRunAt: dto.next_run_at,
  };
}

function toJobRun(dto: LiveJobRunDto): JobRunEntry {
  return {
    id: dto.id,
    scheduledJobId: dto.scheduled_job_id,
    status: dto.status,
    attempts: dto.attempts,
    runAt: dto.run_at,
    startedAt: dto.started_at,
    finishedAt: dto.finished_at,
    error: dto.error,
  };
}

function toNotification(dto: LiveNotificationDto): NotificationEntry {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    recipientId: dto.recipient_id,
    type: dto.type,
    title: dto.title,
    body: dto.body,
    status: dto.status,
    createdAt: dto.created_at,
    readAt: dto.read_at,
  };
}

interface LiveServiceStatusDto {
  name: string;
  status: string;
  version: string | null;
  latency_ms: number | null;
  error: string | null;
}

function toServiceStatus(dto: LiveServiceStatusDto): ServiceStatus {
  return {
    id: dto.name,
    name: dto.name,
    status: dto.status as ServiceStatus["status"],
    version: dto.version,
    latencyMs: dto.latency_ms,
    error: dto.error,
  };
}

const liveOpsClient = {
  getOverview: () => adminFetchJson<OpsOverview>("/api/v1/admin/ops/overview"),
  getSystemStatus: () =>
    adminFetchJson<{ overall: string; services: LiveServiceStatusDto[] }>("/api/v1/admin/ops/status").then(
      (dto) => ({ overall: dto.overall, services: dto.services.map(toServiceStatus) }),
    ),
  getIsolationCheck: () => adminFetchJson<IsolationCheck>("/api/v1/admin/ops/isolation"),
  getAudit: (filters?: AuditFilters) => {
    const query = new URLSearchParams();
    if (filters?.action) query.set("action", filters.action);
    if (filters?.entityType) query.set("entity_type", filters.entityType);
    if (filters?.entityId) query.set("entity_id", filters.entityId);
    if (filters?.requestId) query.set("request_id", filters.requestId);
    if (filters?.limit) query.set("limit", String(filters.limit));
    return adminFetchJson<LiveAuditDto[]>(`/api/v1/admin/audit?${query.toString()}`).then((rows) =>
      rows.map(toAuditEntry),
    );
  },
  getQueue: (filters?: QueueFilters) => {
    const query = new URLSearchParams();
    if (filters?.queue) query.set("queue", filters.queue);
    if (filters?.state) query.set("state", filters.state);
    if (filters?.limit) query.set("limit", String(filters.limit));
    return adminFetchJson<LiveQueueDto[]>(`/api/v1/admin/queue?${query.toString()}`).then((rows) =>
      rows.map(toQueueItem),
    );
  },
  retryQueueItem: (id: string) =>
    adminFetchJson<LiveQueueDto>(`/api/v1/admin/queue/${id}/retry`, { method: "POST" }).then(toQueueItem),
  getWebhookLogs: (filters?: LogFilters) => {
    const query = new URLSearchParams();
    if (filters?.source) query.set("source", filters.source);
    if (filters?.status) query.set("status", filters.status);
    return adminFetchJson<LiveWebhookDto[]>(`/api/v1/admin/logs/webhooks?${query.toString()}`).then(
      (rows) => rows.map(toWebhookEntry),
    );
  },
  getOperationLogs: (filters?: LogFilters) => {
    const query = new URLSearchParams();
    if (filters?.operation) query.set("operation", filters.operation);
    if (filters?.status) query.set("status", filters.status);
    return adminFetchJson<LiveOperationDto[]>(`/api/v1/admin/logs/operations?${query.toString()}`).then(
      (rows) => rows.map(toOperationEntry),
    );
  },
  getJobs: () => adminFetchJson<LiveJobDto[]>("/api/v1/admin/jobs").then((rows) => rows.map(toScheduledJob)),
  getJobRuns: (status?: string) => {
    const query = new URLSearchParams();
    if (status) query.set("status", status);
    return adminFetchJson<LiveJobRunDto[]>(`/api/v1/admin/jobs/runs?${query.toString()}`).then((rows) =>
      rows.map(toJobRun),
    );
  },
  getNotifications: () =>
    adminFetchJson<LiveNotificationDto[]>("/api/v1/admin/notifications").then((rows) => rows.map(toNotification)),
  markNotificationRead: (id: string) =>
    adminFetchJson<LiveNotificationDto>(`/api/v1/admin/notifications/${id}/read`, { method: "POST" }).then(
      toNotification,
    ),
};

// ------------------------------------------------------- live automation client
const AUTOMATION_API_BASE = process.env.NEXT_PUBLIC_AUTOMATION_API_BASE_URL ?? "";

function automationFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  return fetch(`${AUTOMATION_API_BASE}${path}`, {
    ...init,
    headers: { ...liveHeaders(), ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`Automation API request failed: ${response.status} ${response.statusText}`);
    }
    return (await response.json()) as T;
  });
}

interface LiveAutomationRuleDto {
  id: string;
  niche_id: string | null;
  code: string;
  trigger_type: string;
  status: string;
  run_as_user_id: string | null;
  created_at: string;
  updated_at: string;
}

interface LiveScheduledJobDto {
  id: string;
  niche_id: string | null;
  job_key: string;
  cron_expr: string;
  queue: string;
  handler: string;
  status: string;
  last_run_at: string | null;
  next_run_at: string | null;
}

interface LiveJobRunDetailDto {
  id: string;
  niche_id: string | null;
  niche_slug: string | null;
  scheduled_job_id: string;
  job_key: string;
  run_at: string;
  status: string;
  attempts: number;
  started_at: string | null;
  finished_at: string | null;
  output_ref: string | null;
  error: string | null;
}

interface LiveQueueItemDetailDto {
  id: string;
  niche_id: string | null;
  niche_slug: string | null;
  queue: string;
  payload_ref: string;
  state: string;
  attempts: number;
  max_attempts: number;
  run_at: string;
  completed_at: string | null;
  error: string | null;
}

interface LiveExecutorDto {
  name: string;
  queue: string;
}

function toExecutor(dto: LiveExecutorDto): AdminExecutor {
  return { id: dto.name, name: dto.name, queue: dto.queue };
}

function toAutomationRule(dto: LiveAutomationRuleDto): AdminAutomationRule {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    code: dto.code,
    triggerType: dto.trigger_type,
    status: dto.status,
    runAsUserId: dto.run_as_user_id,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

function toAutomationJob(dto: LiveScheduledJobDto): AdminScheduledJob {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    jobKey: dto.job_key,
    cronExpr: dto.cron_expr,
    queue: dto.queue,
    handler: dto.handler,
    status: dto.status,
    lastRunAt: dto.last_run_at,
    nextRunAt: dto.next_run_at,
  };
}

function toJobRunDetail(dto: LiveJobRunDetailDto): AdminJobRunDetail {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    nicheSlug: dto.niche_slug,
    scheduledJobId: dto.scheduled_job_id,
    jobKey: dto.job_key,
    runAt: dto.run_at,
    status: dto.status,
    attempts: dto.attempts,
    startedAt: dto.started_at,
    finishedAt: dto.finished_at,
    outputRef: dto.output_ref,
    error: dto.error,
  };
}

function toQueueItemDetail(dto: LiveQueueItemDetailDto): AdminQueueItemDetail {
  return {
    id: dto.id,
    nicheId: dto.niche_id,
    nicheSlug: dto.niche_slug,
    queue: dto.queue,
    payloadRef: dto.payload_ref,
    state: dto.state,
    attempts: dto.attempts,
    maxAttempts: dto.max_attempts,
    runAt: dto.run_at,
    completedAt: dto.completed_at,
    error: dto.error,
  };
}

interface LiveRunEnvelopeDto {
  run: LiveJobRunDetailDto;
  queue_item: LiveQueueItemDetailDto;
}

function toRunEnvelope(dto: LiveRunEnvelopeDto): { run: AdminJobRunDetail; queueItem: AdminQueueItemDetail } {
  return { run: toJobRunDetail(dto.run), queueItem: toQueueItemDetail(dto.queue_item) };
}

const liveAutomationClient = {
  getRules: () => automationFetchJson<LiveAutomationRuleDto[]>("/api/v1/admin/rules").then((rows) => rows.map(toAutomationRule)),
  enableRule: (id: string) =>
    automationFetchJson<LiveAutomationRuleDto>(`/api/v1/admin/rules/${id}/enable`, { method: "POST" }).then(toAutomationRule),
  disableRule: (id: string) =>
    automationFetchJson<LiveAutomationRuleDto>(`/api/v1/admin/rules/${id}/disable`, { method: "POST" }).then(toAutomationRule),
  getJobs: () => automationFetchJson<LiveScheduledJobDto[]>("/api/v1/admin/scheduled-jobs").then((rows) => rows.map(toAutomationJob)),
  runJob: (id: string, config?: Record<string, unknown>) =>
    automationFetchJson<LiveRunEnvelopeDto>(`/api/v1/admin/scheduled-jobs/${id}/enqueue`, {
      method: "POST",
      body: JSON.stringify({ config: config ?? {} }),
    }).then(toRunEnvelope),
  getJobRuns: (status?: string) => {
    const query = new URLSearchParams();
    if (status) query.set("status", status);
    return automationFetchJson<LiveJobRunDetailDto[]>(`/api/v1/admin/jobs/runs?${query.toString()}`).then((rows) =>
      rows.map(toJobRunDetail),
    );
  },
  retryRun: (id: string) =>
    automationFetchJson<LiveRunEnvelopeDto>(`/api/v1/admin/job-runs/${id}/retry`, { method: "POST" }).then(toRunEnvelope),
  cancelRun: (id: string) =>
    automationFetchJson<LiveJobRunDetailDto>(`/api/v1/admin/job-runs/${id}/cancel`, { method: "POST" }).then(toJobRunDetail),
  getQueue: (state?: string) => {
    const query = new URLSearchParams();
    if (state) query.set("state", state);
    return automationFetchJson<LiveQueueItemDetailDto[]>(`/api/v1/admin/queue/detailed?${query.toString()}`).then((rows) =>
      rows.map(toQueueItemDetail),
    );
  },
  retryQueueItem: (id: string) =>
    automationFetchJson<LiveQueueItemDetailDto>(`/api/v1/admin/queue/${id}/retry`, { method: "POST" }).then(toQueueItemDetail),
  cancelQueueItem: (id: string) =>
    automationFetchJson<LiveQueueItemDetailDto>(`/api/v1/admin/queue/${id}/cancel`, { method: "POST" }).then(toQueueItemDetail),
  getExecutors: () =>
    automationFetchJson<LiveExecutorDto[]>("/api/v1/admin/executors").then((rows) => rows.map(toExecutor)),
};

const liveAdminApiClient: AdminApiClient = {
  dashboard: mockAdminApiClient.dashboard,
  analytics: liveAnalyticsClient,
  pinterest: mockAdminApiClient.pinterest,
  automation: liveAutomationClient,
  content: liveContentClient,
  affiliate: liveAffiliateClient,
  ops: liveOpsClient,
};

export function createAdminApiClient(): AdminApiClient {
  return CONTENT_API_BASE || AFFILIATE_API_BASE || ANALYTICS_API_BASE || ADMIN_API_BASE || AUTOMATION_API_BASE
    ? liveAdminApiClient
    : mockAdminApiClient;
}

export { PAGE_TITLES };
