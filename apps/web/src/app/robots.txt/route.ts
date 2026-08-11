import { createApiClient } from "@/lib/api-client";
import { SITE } from "@/lib/site";

export const revalidate = 3600;

/**
 * robots.txt (M7 §5): served by seo-service per niche. The site origin
 * proxies the applied rules so crawlers (including Pinterestbot) always see
 * the frozen policy. The static fallback keeps standalone builds crawlable.
 */
export async function GET() {
  const robots = await createApiClient().seo.getRobots();
  const text =
    robots ??
    [
      "User-agent: *",
      "Allow: /",
      "Disallow: /admin",
      "Disallow: /api/",
      "Disallow: /search",
      `Sitemap: ${SITE.url}/sitemap.xml`,
      "",
    ].join("\n");
  return new Response(text, {
    headers: { "content-type": "text/plain; charset=utf-8" },
  });
}
