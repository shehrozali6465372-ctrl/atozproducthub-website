import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const SEARCH_DTO = {
  items: [
    {
      id: "art-1",
      type: "article",
      slug: "kitchen-guide",
      title: "Kitchen Guide",
      excerpt: "An excerpt.",
      url: "/articles/kitchen-guide",
      score: 12.5,
    },
    {
      id: "prod-1",
      type: "product",
      slug: "stainless-pan",
      title: "Stainless Pan",
      excerpt: "Cookware.",
      url: "/products/stainless-pan",
      score: 9.1,
    },
  ],
  page: 1,
  page_size: 20,
  total: 2,
};

const METADATA_DTO = {
  title: "Kitchen Guide",
  description: "Everything kitchen.",
  canonical_url: "https://atozproducthub.dev/articles/kitchen-guide",
  robots: "index,follow",
  og: { type: "article" },
  structured_data: [{ "@type": "Article", headline: "Kitchen Guide" }],
};

describe("live SEO API client (M7)", () => {
  const originalBase = process.env.NEXT_PUBLIC_SEO_API_BASE_URL;
  const originalNiche = process.env.NEXT_PUBLIC_NICHE_SLUG;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_SEO_API_BASE_URL = "http://seo.test";
    process.env.NEXT_PUBLIC_NICHE_SLUG = "kitchen";
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_SEO_API_BASE_URL = originalBase;
    process.env.NEXT_PUBLIC_NICHE_SLUG = originalNiche;
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("maps search hits from the niche-scoped search API", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      expect(url).toContain("/api/v1/public/search?niche=kitchen");
      expect(url).toContain("q=guide");
      return { ok: true, json: async () => SEARCH_DTO };
    });
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    const result = await createApiClient().seo.search("guide");
    expect(result.hits).toHaveLength(2);
    expect(result.hits[0]).toMatchObject({
      type: "article",
      title: "Kitchen Guide",
      url: "/articles/kitchen-guide",
    });
    expect(result.hits[1].type).toBe("product");
  });

  it("maps applied SEO metadata for a public path", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      expect(url).toContain("/api/v1/public/seo/meta?niche=kitchen");
      expect(url).toContain("path=%2Farticles%2Fkitchen-guide");
      return { ok: true, json: async () => METADATA_DTO };
    });
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    const meta = await createApiClient().seo.getMetadata("/articles/kitchen-guide");
    expect(meta).toMatchObject({
      title: "Kitchen Guide",
      canonicalUrl: "https://atozproducthub.dev/articles/kitchen-guide",
      robots: "index,follow",
    });
    expect(meta?.structuredData).toEqual([{ "@type": "Article", headline: "Kitchen Guide" }]);
  });

  it("returns null for missing metadata instead of throwing", async () => {
    const fetchMock = vi.fn(async () => ({ ok: false, status: 404, statusText: "Not Found" }));
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    expect(await createApiClient().seo.getMetadata("/nope")).toBeNull();
  });
});
