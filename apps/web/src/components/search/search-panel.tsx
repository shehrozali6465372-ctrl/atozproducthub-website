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
import type { Article, Product } from "@/lib/api-client";

type ResultType = "all" | "articles" | "products";

const FILTER_OPTIONS: FilterOption[] = [
  { value: "all", label: "All" },
  { value: "articles", label: "Articles" },
  { value: "products", label: "Products" },
];

/** Search wireframe: query + type filter over mock data (UI-only). */
export function SearchPanel({
  query,
  articles,
  products,
}: {
  query: string;
  articles: Article[];
  products: Product[];
}) {
  const [activeFilter, setActiveFilter] = useState<ResultType>("all");
  const [activeQuery, setActiveQuery] = useState(query);

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
  const hasQuery = activeQuery.trim().length > 0;
  const hasResults = visibleArticles.length > 0 || visibleProducts.length > 0;

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
          description="Real search arrives with Typesense in a later milestone. For now, try one of the sample topics above."
        />
      ) : (
        <div className="space-y-8">
          {visibleArticles.length > 0 ? (
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
          {visibleProducts.length > 0 ? (
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
