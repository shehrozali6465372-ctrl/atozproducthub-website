import type { SeoMetadata } from "@/lib/api-client";

/**
 * Renders the JSON-LD structured data produced by seo-service (Article,
 * Product, BreadcrumbList, CollectionPage). The data is validated business
 * output — it is never AI-generated inside the website (Website Contract).
 */
export function SeoJsonLd({ seo }: { seo: SeoMetadata | null }) {
  if (!seo || seo.structuredData.length === 0) return null;
  return (
    <>
      {seo.structuredData.map((block, index) => (
        <script
          key={`jsonld-${index}`}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(block) }}
        />
      ))}
    </>
  );
}
