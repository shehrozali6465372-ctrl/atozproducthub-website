import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  Badge,
  Breadcrumbs,
  Container,
  ContentCard,
  Pagination,
  SectionHeading,
} from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const category = await createApiClient().content
    .listCategories()
    .then((items) => items.find((item) => item.slug === slug));
  return { title: category?.name ?? "Category", description: category?.description };
}

export default async function CategoryPage({ params }: PageProps) {
  const { slug } = await params;
  const api = createApiClient();
  const [categories, articles] = await Promise.all([
    api.content.listCategories(),
    api.content.listArticles(),
  ]);
  const category = categories.find((item) => item.slug === slug);
  if (!category) notFound();

  const filtered = articles.filter((article) => article.category === category.name);

  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs
        className="mb-6"
        items={[{ label: "Home", href: "/" }, { label: "Categories" }, { label: category.name }]}
      />
      <SectionHeading
        eyebrow="Category"
        title={category.name}
        description={category.description}
      />
      {filtered.length === 0 ? (
        <p className="text-sm text-text-600">
          No articles published in this category yet — content ships with the CMS milestone.
        </p>
      ) : (
        <>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((article) => (
              <ContentCard
                key={article.slug}
                title={article.title}
                description={article.excerpt}
                meta={`${article.readTime} · ${article.publishedAt}`}
                href={`/articles/${article.slug}`}
                badge={<Badge variant="neutral">{article.category}</Badge>}
              />
            ))}
          </div>
          <Pagination className="mt-10" page={1} totalPages={1} onPageChange={() => undefined} />
        </>
      )}
    </Container>
  );
}
