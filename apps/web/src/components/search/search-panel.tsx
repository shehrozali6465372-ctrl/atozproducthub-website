"use client";

import { useMemo, useState } from "react";
import {
  Badge,
  ContentCard,
  EmptyState,
  FilterBar,
  Pagination,
  SearchInput,
  type FilterOption,
} from "@atoz/design-system";
import type { Article, Product, SearchHit } from "@/lib/api-client";

type ResultType = "all" | "articles" | "products";

const FILTER_OPTIONS: FilterOption[] = [
  { value: "all", label: "All" },
  { value: "articles", label: "Articles" },
  { value: "products", label: "Products" },
];

/**
 * Search results panel. When the SEO service is configured the page passes
 * real search hits (niche-scoped Typesense search via seo-service); without
 * it the panel falls back to the M2 mock filtering path.
 */
export function SearchPanel({
  query,
  articles,
  products,
  hits = [],
}: {
  query: string;
  articles: Article[];
  products: Product[];
  hits?: SearchHit[];
}) {
  const [activeFilter, setActiveFilter] = useState<ResultType>("all");
  const [activeQuery, setActiveQuery] = useState(query);

  const hasLiveHits = hits.length > 0;

  const filtered = useMemo(() => {
    const q = activeQuery.trim().toLowerCase();
    if (!q) return { articles: [], products: [] };
    const matches = (text: string) => text.toLowerCase().includes(q);
    return {
      articles: articles.filter((a) => matches(`${a.title} ${a.excerpt} ${a.tags.join(" ")}`)),
      products: products.filter((p) => matches(`${p.name} ${p.summary}`)),
    };
  }, [activeQuery, articles, products]);

  const showAll = activeFilter === "all";
  const visibleArticles = showAll || activeFilter === "articles" ? filtered.articles : [];
  const visibleProducts = showAll || activeFilter === "products" ? filtered.products : [];
  const visibleHits = useMemo(
    () =>
      hasLiveHits
        ? hits.filter((hit) => {
            if (activeFilter === "all") return true;
            return hit.type === (activeFilter === "articles" ? "article" : "product");
          })
        : [],
    [activeFilter, hasLiveHits, hits],
  );
  const hasQuery = activeQuery.trim().length > 0;
  const hasResults =
    visibleHits.length > 0 || visibleArticles.length > 0 || visibleProducts.length > 0;

  const hitSections = useMemo(() => {
    const groups = new Map<string, SearchHit[]>();
    for (const hit of visibleHits) {
      const current = groups.get(hit.type) ?? [];
      current.push(hit);
      groups.set(hit.type, current);
    }
    return [...groups.entries()];
  }, [visibleHits]);

  return (
    <div className="space-y-6">
      <SearchInput defaultValue={query} onSubmit={setActiveQuery} />
      <FilterBar
        options={FILTER_OPTIONS}
        active={activeFilter}
        onChange={(value) => setActiveFilter(value as ResultType)}
      />

      {!hasQuery ? (
        <EmptyState
          title="Search articles and products"
          description="Try a topic like 'kitchen gadgets', 'home office', or 'travel'."
        />
      ) : !hasResults ? (
        <EmptyState
          title={`No results for “${activeQuery}”`}
          description="Try a different keyword or one of the sample topics above."
        />
      ) : (
        <div className="space-y-8">
          {hitSections.length > 0
            ? hitSections.map(([type, sectionHits]) => (
                <section key={type} aria-labelledby={`search-${type}`}>
                  <h2
                    id={`search-${type}`}
                    className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-400"
                  >
                    {type === "article" ? "Articles" : `${type[0].toUpperCase()}${type.slice(1)}s`} (
                    {sectionHits.length})
                  </h2>
                  <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {sectionHits.map((hit) => (
                      <ContentCard
                        key={`${hit.type}-${hit.id}`}
                        title={hit.title}
                        description={hit.excerpt}
                        href={hit.url}
                        badge={
                          hit.type === "product" ? <Badge variant="accent">Affiliate</Badge> : undefined
                        }
                      />
                    ))}
                  </div>
                </section>
              ))
            : null}
          {!hasLiveHits && visibleArticles.length > 0 ? (
            <section aria-labelledby="search-articles">
              <h2
                id="search-articles"
                className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-400"
              >
                Articles ({visibleArticles.length})
              </h2>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {visibleArticles.map((article) => (
                  <ContentCard
                    key={article.slug}
                    title={article.title}
                    description={article.excerpt}
                    meta={article.readTime}
                    href={`/articles/${article.slug}`}
                  />
                ))}
              </div>
            </section>
          ) : null}
          {!hasLiveHits && visibleProducts.length > 0 ? (
            <section aria-labelledby="search-products">
              <h2
                id="search-products"
                className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-400"
              >
                Products ({visibleProducts.length})
              </h2>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {visibleProducts.map((product) => (
                  <ContentCard
                    key={product.slug}
                    title={product.name}
                    description={product.summary}
                    meta={product.price}
                    href={`/products/${product.slug}`}
                    badge={<Badge variant="accent">Affiliate</Badge>}
                  />
                ))}
              </div>
            </section>
          ) : null}
          <Pagination page={1} totalPages={1} onPageChange={() => undefined} />
        </div>
      )}
    </div>
  );
}
