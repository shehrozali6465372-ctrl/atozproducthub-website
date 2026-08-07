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
 * Typed API client — M2 foundation stub.
 *
 * Mirrors the shape of the Public Read API (12-api-contracts.md) so pages
 * depend on an interface, not on mock internals. In Phase 6 this is replaced
 * by a contract-generated client over `libs/contracts/` that talks to the
 * API gateway. No real network calls exist in M2.
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

export function createApiClient(): ApiClient {
  return mockApiClient;
}
