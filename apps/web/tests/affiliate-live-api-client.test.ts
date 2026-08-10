import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const PRODUCT_DTO = {
  id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  slug: "stainless-pan",
  name: "Stainless Steel Pan",
  excerpt: "A reliable do-everything pan.",
  price_cents: 4500,
  currency: "USD",
  category: { slug: "cookware", name: "Cookware", path: "Kitchen > Cookware" },
  merchant_name: "Acme Kitchen Co.",
  network_name: "Amazon Associates",
  disclosure_required: true,
  buy_url: "/api/v1/public/go/signed-token",
};

const CATEGORY_DTO = { slug: "cookware", name: "Cookware", path: "Kitchen > Cookware" };

describe("live affiliate API client (M5)", () => {
  const originalBase = process.env.NEXT_PUBLIC_AFFILIATE_API_BASE_URL;
  const originalNiche = process.env.NEXT_PUBLIC_NICHE_SLUG;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_AFFILIATE_API_BASE_URL = "http://affiliate.test";
    process.env.NEXT_PUBLIC_NICHE_SLUG = "kitchen";
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_AFFILIATE_API_BASE_URL = originalBase;
    process.env.NEXT_PUBLIC_NICHE_SLUG = originalNiche;
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("maps a public product DTO to the page product shape with an absolute go URL", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      expect(url).toContain("/api/v1/public/products?niche=kitchen");
      return { ok: true, json: async () => ({ items: [PRODUCT_DTO], page: 1, page_size: 100, total: 1 }) };
    });
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    const [product] = await createApiClient().affiliate.listProducts();
    expect(product).toMatchObject({
      slug: "stainless-pan",
      name: "Stainless Steel Pan",
      price: "$45.00",
      summary: "A reliable do-everything pan.",
      disclosureRequired: true,
    });
    // The go path must be resolved against the affiliate API base so the
    // server-controlled redirect is always fetched from the right origin.
    expect(product.buyUrl).toBe("http://affiliate.test/api/v1/public/go/signed-token");
  });

  it("maps product categories to collection cards", async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => [CATEGORY_DTO] }));
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    const collections = await createApiClient().affiliate.listCollections();
    expect(collections).toEqual([
      { slug: "cookware", title: "Cookware", description: "Kitchen > Cookware", productCount: 0 },
    ]);
  });

  it("returns null for a missing product instead of throwing", async () => {
    const fetchMock = vi.fn(async () => ({ ok: false, status: 404, statusText: "Not Found" }));
    vi.stubGlobal("fetch", fetchMock);
    const { createApiClient } = await import("@/lib/api-client");
    expect(await createApiClient().affiliate.getProduct("missing")).toBeNull();
  });

  it("keeps mock fixtures when no affiliate base URL is configured", async () => {
    process.env.NEXT_PUBLIC_AFFILIATE_API_BASE_URL = "";
    const { createApiClient } = await import("@/lib/api-client");
    const products = await createApiClient().affiliate.listProducts();
    expect(products.length).toBeGreaterThan(0);
    expect(products.some((p) => p.slug === "sample-product")).toBe(true);
  });
});
