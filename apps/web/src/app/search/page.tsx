import type { Metadata } from "next";
import { Breadcrumbs, Container, SectionHeading } from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";
import { SearchPanel } from "@/components/search/search-panel";

export const metadata: Metadata = {
  title: "Search",
  description: "Find articles and products across AtozProductHub.",
  robots: { index: false, follow: true },
};

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  const api = createApiClient();
  const query = q?.trim() ?? "";
  // Real niche-scoped search comes from seo-service (M7); without
  // NEXT_PUBLIC_SEO_API_BASE_URL the seo client falls back to mock filtering.
  const [articles, products, results] = await Promise.all([
    api.content.listArticles(),
    api.affiliate.listProducts(),
    api.seo.search(query),
  ]);

  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs
        className="mb-6"
        items={[{ label: "Home", href: "/" }, { label: "Search" }]}
      />
      <SectionHeading
        title="Search"
        description="Find articles and products across AtozProductHub."
      />
      <SearchPanel query={query} articles={articles} products={products} hits={results.hits} />
    </Container>
  );
}
