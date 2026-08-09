import {
  AUTOMATION_RULES,
  DASHBOARD_KPIS,
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
};

// ------------------------------------------------------------------ live mode
const CONTENT_API_BASE = process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL ?? "";

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

const liveAdminApiClient: AdminApiClient = {
  dashboard: mockAdminApiClient.dashboard,
  analytics: mockAdminApiClient.analytics,
  pinterest: mockAdminApiClient.pinterest,
  automation: mockAdminApiClient.automation,
  content: liveContentClient,
};

export function createAdminApiClient(): AdminApiClient {
  return CONTENT_API_BASE ? liveAdminApiClient : mockAdminApiClient;
}

export { PAGE_TITLES };
