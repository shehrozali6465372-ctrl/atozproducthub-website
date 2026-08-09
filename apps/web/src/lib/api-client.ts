import {
  MOCK_ARTICLES,
  MOCK_CATEGORIES,
  MOCK_COLLECTIONS,
  MOCK_LANDING_PAGES,
  MOCK_PINS,
  MOCK_PRODUCTS,
  MOCK_TAGS,
  type MockArticle,
  type MockCategory,
  type MockCollection,
  type MockPin,
  type MockProduct,
  type MockTag,
} from "./mock-data";

/**
 * Typed API client for the public website.
 *
 * M4: the content namespace now talks to the real content-service Public
 * Read API (12-api-contracts.md §3-4) when NEXT_PUBLIC_CONTENT_API_BASE_URL
 * is set. Without the env var the client keeps the M2 mock fixtures, so the
 * site builds and runs standalone. The affiliate/pinterest namespaces remain
 * mock-based until their milestones — M4 is CMS-only.
 *
 * The website never talks to an AI model: all intelligence arrives through
 * the AI OS Bridge (Website Contract §4).
 */

export type Article = MockArticle;
export type Category = MockCategory;
export type Tag = MockTag;
export type Collection = MockCollection;
export type Product = MockProduct;
export type Pin = MockPin;

export interface SearchResult {
  articles: Article[];
  products: Product[];
}

export interface ApiClient {
  content: {
    listArticles(): Promise<Article[]>;
    getArticle(slug: string): Promise<Article | null>;
    listCategories(): Promise<Category[]>;
    listTags(): Promise<Tag[]>;
    search(query: string): Promise<SearchResult>;
  };
  affiliate: {
    listCollections(): Promise<Collection[]>;
    getCollection(slug: string): Promise<Collection | null>;
    listProducts(): Promise<Product[]>;
    getProduct(slug: string): Promise<Product | null>;
  };
  pinterest: {
    listRecentPins(): Promise<Pin[]>;
    getLandingPage(slug: string): Promise<{ title: string; intro: string; articles: Article[]; pins: Pin[] } | null>;
  };
}

// ------------------------------------------------------------ live API DTOs
interface PublicCategoryDto {
  slug: string;
  name: string;
  description: string;
}

interface PublicTagDto {
  slug: string;
  name: string;
}

interface PublicArticleDto {
  id: string;
  slug: string;
  title: string;
  excerpt: string;
  category: PublicCategoryDto | null;
  tags: PublicTagDto[];
  read_time_minutes: number;
  published_at: string;
  body: string[];
}

interface PageDto<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

const CONTENT_API_BASE = process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL ?? "";
const NICHE_SLUG = process.env.NEXT_PUBLIC_NICHE_SLUG ?? "kitchen";

function formatPublishedAt(value: string): string {
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function toArticle(dto: PublicArticleDto): Article {
  return {
    slug: dto.slug,
    title: dto.title,
    excerpt: dto.excerpt,
    category: dto.category?.name ?? "General",
    categoryHref: `/categories/${dto.category?.slug ?? "general"}`,
    tags: dto.tags.map((tag) => tag.slug),
    readTime: `${dto.read_time_minutes} min read`,
    publishedAt: formatPublishedAt(dto.published_at),
    body: dto.body,
  };
}

// -------------------------------------------------------------- mock client
const delay = <T>(value: T): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), 0));

const mockApiClient: ApiClient = {
  content: {
    listArticles: () => delay(MOCK_ARTICLES),
    getArticle: (slug) => delay(MOCK_ARTICLES.find((a) => a.slug === slug) ?? null),
    listCategories: () => delay(MOCK_CATEGORIES),
    listTags: () => delay(MOCK_TAGS),
    search: (query) =>
      delay({
        articles: MOCK_ARTICLES.filter((a) =>
          `${a.title} ${a.excerpt}`.toLowerCase().includes(query.toLowerCase()),
        ),
        products: MOCK_PRODUCTS.filter((p) =>
          p.name.toLowerCase().includes(query.toLowerCase()),
        ),
      }),
  },
  affiliate: {
    listCollections: () => delay(MOCK_COLLECTIONS),
    getCollection: (slug) => delay(MOCK_COLLECTIONS.find((c) => c.slug === slug) ?? null),
    listProducts: () => delay(MOCK_PRODUCTS),
    getProduct: (slug) => delay(MOCK_PRODUCTS.find((p) => p.slug === slug) ?? null),
  },
  pinterest: {
    listRecentPins: () => delay(MOCK_PINS),
    getLandingPage: (slug) => delay(MOCK_LANDING_PAGES[slug] ?? null),
  },
};

// -------------------------------------------------------------- live client
async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
    cache: "force-cache",
    next: { revalidate: 3600 },
  });
  if (!response.ok) {
    throw new Error(`Content API request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

const liveContentClient = {
  async listArticles(): Promise<Article[]> {
    const data = await fetchJson<PageDto<PublicArticleDto>>(
      `${CONTENT_API_BASE}/api/v1/public/articles?niche=${encodeURIComponent(NICHE_SLUG)}&page_size=100`,
    );
    return data.items.map(toArticle);
  },
  async getArticle(slug: string): Promise<Article | null> {
    try {
      const data = await fetchJson<PublicArticleDto>(
        `${CONTENT_API_BASE}/api/v1/public/articles/${encodeURIComponent(slug)}?niche=${encodeURIComponent(NICHE_SLUG)}`,
      );
      return toArticle(data);
    } catch {
      return null;
    }
  },
  async listCategories(): Promise<Category[]> {
    const data = await fetchJson<PublicCategoryDto[]>(
      `${CONTENT_API_BASE}/api/v1/public/categories?niche=${encodeURIComponent(NICHE_SLUG)}`,
    );
    return data.map((item) => ({ slug: item.slug, name: item.name, description: item.description }));
  },
  async listTags(): Promise<Tag[]> {
    const data = await fetchJson<PublicTagDto[]>(
      `${CONTENT_API_BASE}/api/v1/public/tags?niche=${encodeURIComponent(NICHE_SLUG)}`,
    );
    return data.map((item) => ({ slug: item.slug, name: item.name }));
  },
  async search(query: string): Promise<SearchResult> {
    const normalized = query.toLowerCase();
    const articles = (await liveContentClient.listArticles()).filter((article) =>
      `${article.title} ${article.excerpt}`.toLowerCase().includes(normalized),
    );
    // Product search stays mock-backed until the affiliate milestone (M5+).
    const products = MOCK_PRODUCTS.filter((p) => p.name.toLowerCase().includes(normalized));
    return { articles, products };
  },
};

const liveApiClient: ApiClient = {
  content: liveContentClient,
  affiliate: mockApiClient.affiliate,
  pinterest: mockApiClient.pinterest,
};

export function createApiClient(): ApiClient {
  return CONTENT_API_BASE ? liveApiClient : mockApiClient;
}
