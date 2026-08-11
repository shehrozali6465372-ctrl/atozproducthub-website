import type { Metadata } from "next";
import type { SeoMetadata } from "@/lib/api-client";

/**
 * Apply seo-service metadata (M7 §3) to a page's Next Metadata.
 *
 * The SEO service is the source of truth for canonical URLs, robots rules,
 * Open Graph and JSON-LD (applied business output from the AI OS Bridge).
 * When the service is not configured the page falls back to its own
 * wireframe metadata so standalone builds stay crawlable.
 */
export function mergeSeoMetadata(
  seo: SeoMetadata | null,
  fallback: Metadata,
): Metadata {
  if (!seo) return fallback;
  return {
    ...fallback,
    title: seo.title || fallback.title,
    description: seo.description || fallback.description,
    alternates: {
      ...fallback.alternates,
      canonical: seo.canonicalUrl || fallback.alternates?.canonical,
    },
    robots: seo.robots ? robotsPolicy(seo.robots) : fallback.robots,
    openGraph: {
      ...fallback.openGraph,
      title: seo.title || fallback.openGraph?.title,
      description: seo.description || fallback.openGraph?.description,
      url: seo.canonicalUrl || fallback.openGraph?.url,
    },
  };
}

export function robotsPolicy(robots: string): Metadata["robots"] {
  const tokens = robots.toLowerCase().split(",").map((token) => token.trim());
  const index = tokens.includes("noindex") ? false : true;
  const follow = tokens.includes("nofollow") ? false : true;
  return index === false || follow === false ? { index, follow } : undefined;
}
