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
 * M4/M5: the content and affiliate namespaces talk to the real content and
 * affiliate service Public Read APIs when their base URLs are set. Without
 * the env vars the client keeps the M2 mock fixtures, so the site builds and
 * runs standalone. The pinterest namespace (M6) follows the same rule.
 * The seo namespace (M7) talks to the seo-service Public Read API (search,
 * metadata, robots, sitemaps) when ``NEXT_PUBLIC_SEO_API_BASE_URL`` is set.
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
  /** Unified hits from the SEO service search API (M7) when configured. */
  hits: SearchHit[];
}

export interface SearchHit {
  id: string;
  type: string;
  slug: string;
  title: string;
  excerpt: string;
  url: string;
  score: number;
}

export interface SeoMetadata {
  title: string;
  description: string;
  canonicalUrl: string;
  robots: string;
  og: Record<string, unknown>;
  structuredData: unknown[];
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
  seo: {
    search(query: string, type?: string): Promise<SearchResult>;
    getMetadata(path: string): Promise<SeoMetadata | null>;
    getRobots(): Promise<string | null>;
    getSitemap(filename: string): Promise<string | null>;
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

interface PublicPinDto {
  id: string;
  slug: string;
  title: string;
  description: string;
  board: string;
  account_name: string;
  destination_url: string;
  pin_url: string;
  published_at: string | null;
  saves: string;
}

const CONTENT_API_BASE = process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL ?? "";
const AFFILIATE_API_BASE = process.env.NEXT_PUBLIC_AFFILIATE_API_BASE_URL ?? "";
const PINTEREST_API_BASE = process.env.NEXT_PUBLIC_PINTEREST_API_BASE_URL ?? "";
const SEO_API_BASE = process.env.NEXT_PUBLIC_SEO_API_BASE_URL ?? "";
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

// -------------------------------------------------- affiliate live DTOs
interface PublicProductCategoryDto {
  slug: string;
  name: string;
  path: string | null;
}

interface PublicProductDto {
  id: string;
  slug: string;
  name: string;
  excerpt: string;
  price_cents: number;
  currency: string;
  category: PublicProductCategoryDto | null;
  merchant_name: string;
  network_name: string;
  disclosure_required: boolean;
  buy_url: string | null;
}

function formatPrice(cents: number, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(cents / 100);
}

function toProduct(dto: PublicProductDto): Product {
  return {
    slug: dto.slug,
    name: dto.name,
    price: formatPrice(dto.price_cents, dto.currency),
    summary: dto.excerpt,
    // The go endpoint returns JSON, so the client component resolves it and
    // navigates; the relative path from the API is made absolute here.
    buyUrl: dto.buy_url
      ? new URL(dto.buy_url, AFFILIATE_API_BASE).toString()
      : undefined,
    disclosureRequired: dto.disclosure_required,
  };
}

const liveAffiliateClient = {
  async listCollections(): Promise<Collection[]> {
    const categories = await fetchJson<PublicProductCategoryDto[]>(
      `${AFFILIATE_API_BASE}/api/v1/public/product-categories?niche=${encodeURIComponent(NICHE_SLUG)}`,
    );
    return categories.map((category) => ({
      slug: category.slug,
      title: category.name,
      description: category.path ?? category.name,
      productCount: 0,
    }));
  },
  async getCollection(slug: string): Promise<Collection | null> {
    const collections = await liveAffiliateClient.listCollections();
    return collections.find((collection) => collection.slug === slug) ?? null;
  },
  async listProducts(): Promise<Product[]> {
    const data = await fetchJson<PageDto<PublicProductDto>>(
      `${AFFILIATE_API_BASE}/api/v1/public/products?niche=${encodeURIComponent(NICHE_SLUG)}&page_size=100`,
    );
    return data.items.map(toProduct);
  },
  async getProduct(slug: string): Promise<Product | null> {
    try {
      const data = await fetchJson<PublicProductDto>(
        `${AFFILIATE_API_BASE}/api/v1/public/products/${encodeURIComponent(slug)}?niche=${encodeURIComponent(NICHE_SLUG)}`,
      );
      return toProduct(data);
    } catch {
      return null;
    }
  },
};

// ------------------------------------------------------------- pinterest
const livePinterestClient: ApiClient["pinterest"] = {
  async listRecentPins(): Promise<Pin[]> {
    const data = await fetchJson<PageDto<PublicPinDto>>(
      `${PINTEREST_API_BASE}/api/v1/public/pins?niche=${encodeURIComponent(NICHE_SLUG)}&limit=100`,
    );
    return data.items.map((pin) => ({
      slug: pin.slug || pin.id,
      title: pin.title,
      board: pin.board || pin.account_name,
      saves: pin.saves || "",
    }));
  },
  async getLandingPage(slug) {
    try {
      const pins = await livePinterestClient.listRecentPins();
      const pin = pins.find((item) => item.slug === slug);
      if (!pin) return null;
      const articles = await liveContentClient.listArticles();
      return {
        title: pin.title,
        intro:
          "You saved a pin — here is the full guide behind it. Honest testing, clear recommendations, and zero hype.",
        articles,
        pins,
      };
    } catch {
      return null;
    }
  },
};

// -------------------------------------------------------------------- seo
interface SeoSearchHitDto {
  id: string;
  type: string;
  slug: string;
  title: string;
  excerpt: string;
  url: string;
  score: number;
}

type SeoSearchPageDto = PageDto<SeoSearchHitDto>;

interface SeoMetadataDto {
  title: string;
  description: string;
  canonical_url: string;
  robots: string;
  og: Record<string, unknown>;
  structured_data: unknown[];
}

const liveSeoClient: ApiClient["seo"] = {
  async search(query: string, type?: string): Promise<SearchResult> {
    if (!query.trim()) return { articles: [], products: [], hits: [] };
    const params = new URLSearchParams({ niche: NICHE_SLUG, q: query });
    if (type) params.set("type", type);
    const data = await fetchJson<SeoSearchPageDto>(
      `${SEO_API_BASE}/api/v1/public/search?${params.toString()}`,
    );
    return { articles: [], products: [], hits: data.items };
  },
  async getMetadata(path: string): Promise<SeoMetadata | null> {
    try {
      const data = await fetchJson<SeoMetadataDto>(
        `${SEO_API_BASE}/api/v1/public/seo/meta?niche=${encodeURIComponent(NICHE_SLUG)}&path=${encodeURIComponent(path)}`,
      );
      return {
        title: data.title,
        description: data.description,
        canonicalUrl: data.canonical_url,
        robots: data.robots,
        og: data.og,
        structuredData: data.structured_data,
      };
    } catch {
      return null;
    }
  },
  async getRobots(): Promise<string | null> {
    try {
      const response = await fetch(
        `${SEO_API_BASE}/api/v1/public/seo/robots?niche=${encodeURIComponent(NICHE_SLUG)}`,
        { headers: { Accept: "text/plain" }, cache: "no-store" },
      );
      if (!response.ok) return null;
      return await response.text();
    } catch {
      return null;
    }
  },
  async getSitemap(filename: string): Promise<string | null> {
    try {
      const response = await fetch(
        `${SEO_API_BASE}/api/v1/public/seo/sitemaps/${encodeURIComponent(filename)}?niche=${encodeURIComponent(NICHE_SLUG)}`,
        { headers: { Accept: "application/xml" }, cache: "no-store" },
      );
      if (!response.ok) return null;
      return await response.text();
    } catch {
      return null;
    }
  },
};

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
        hits: [],
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
  seo: {
    search: (query) => mockApiClient.content.search(query),
    getMetadata: () => delay(null),
    getRobots: () => delay(null),
    getSitemap: () => delay(null),
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
    return { articles, products, hits: [] };
  },
};

export function createApiClient(): ApiClient {
  // Each namespace goes live independently: without its base URL the client
  // keeps the M2 mock fixtures so the site builds and runs standalone.
  return {
    content: CONTENT_API_BASE ? liveContentClient : mockApiClient.content,
    affiliate: AFFILIATE_API_BASE ? liveAffiliateClient : mockApiClient.affiliate,
    pinterest: PINTEREST_API_BASE ? livePinterestClient : mockApiClient.pinterest,
    seo: SEO_API_BASE ? liveSeoClient : mockApiClient.seo,
  };
}
