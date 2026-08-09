import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const ARTICLE_DTO = {
  id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  slug: "kitchen-guide",
  title: "Kitchen Guide",
  excerpt: "An excerpt.",
  category: { slug: "kitchen", name: "Kitchen", description: "Cookware." },
  tags: [
    { slug: "kitchen", name: "Kitchen" },
    { slug: "guide", name: "Guide" },
  ],
  read_time_minutes: 5,
  published_at: "2026-08-02T09:00:00Z",
  body: ["First paragraph.", "Second paragraph."],
};

const CATEGORY_DTO = { slug: "kitchen", name: "Kitchen", description: "Cookware." };
const TAG_DTO = { slug: "guide", name: "Guide" };

describe("live content API client (M4)", () => {
  const originalBase = process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL;
  const originalNiche = process.env.NEXT_PUBLIC_NICHE_SLUG;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL = "http://content.test";
    process.env.NEXT_PUBLIC_NICHE_SLUG = "kitchen";
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_CONTENT_API_BASE_URL = originalBase;
    process.env.NEXT_PUBLIC_NICHE_SLUG = originalNiche;
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("maps a public article DTO to the page article shape", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      expect(url).toContain("/api/v1/public/articles/kitchen-guide?niche=kitchen");
      return { ok: true, json: async () => ARTICLE_DTO };
    });
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    const article = await createApiClient().content.getArticle("kitchen-guide");
    expect(article).not.toBeNull();
    expect(article).toMatchObject({
      slug: "kitchen-guide",
      title: "Kitchen Guide",
      excerpt: "An excerpt.",
      category: "Kitchen",
      categoryHref: "/categories/kitchen",
      tags: ["kitchen", "guide"],
      readTime: "5 min read",
      body: ["First paragraph.", "Second paragraph."],
    });
    expect(article?.publishedAt).toMatch(/Aug 2, 2026/);
  });

  it("lists articles, categories and tags through the public API", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes("/api/v1/public/articles?")) {
        return { ok: true, json: async () => ({ items: [ARTICLE_DTO], page: 1, page_size: 100, total: 1 }) };
      }
      if (url.includes("/api/v1/public/categories?")) {
        return { ok: true, json: async () => [CATEGORY_DTO] };
      }
      if (url.includes("/api/v1/public/tags?")) {
        return { ok: true, json: async () => [TAG_DTO] };
      }
      throw new Error(`Unexpected URL: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    const api = createApiClient();
    const [articles, categories, tags] = await Promise.all([
      api.content.listArticles(),
      api.content.listCategories(),
      api.content.listTags(),
    ]);
    expect(articles).toHaveLength(1);
    expect(categories).toEqual([{ slug: "kitchen", name: "Kitchen", description: "Cookware." }]);
    expect(tags).toEqual([{ slug: "guide", name: "Guide" }]);
  });

  it("returns null for a missing article instead of throwing", async () => {
    const fetchMock = vi.fn(async () => ({ ok: false, status: 404, statusText: "Not Found" }));
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    expect(await createApiClient().content.getArticle("missing")).toBeNull();
  });
});
