import { createApiClient } from "@/lib/api-client";
import { SITE } from "@/lib/site";

export const revalidate = 3600;

const SITEMAP_GROUPS = [
  "articles",
  "categories",
  "tags",
  "products",
  "landing",
  "collections",
] as const;

/**
 * /sitemap.xml (M7 §4): aggregate index pointing at per-group sitemap
 * indexes served by seo-service and proxied at /sitemaps/{group}-index.xml.
 * Only the groups with generated shards are advertised.
 */
export async function GET() {
  const api = createApiClient();
  const available: string[] = [];
  for (const group of SITEMAP_GROUPS) {
    const xml = await api.seo.getSitemap(`${group}-index.xml`);
    if (xml) available.push(group);
  }
  if (available.length === 0) {
    const fallback =
      '<?xml version="1.0" encoding="UTF-8"?>\n' +
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      `  <url><loc>${SITE.url}/</loc></url>\n` +
      "</urlset>\n";
    return new Response(fallback, {
      headers: { "content-type": "application/xml; charset=utf-8" },
    });
  }
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...available.map(
      (group) =>
        `  <sitemap><loc>${SITE.url}/sitemaps/${group}-index.xml</loc></sitemap>`,
    ),
    "</sitemapindex>",
  ];
  return new Response(lines.join("\n") + "\n", {
    headers: { "content-type": "application/xml; charset=utf-8" },
  });
}
