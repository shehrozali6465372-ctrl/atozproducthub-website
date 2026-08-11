import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  Badge,
  Breadcrumbs,
  Card,
  Container,
  ContentCard,
  DisclosureBadge,
  Prose,
  SectionHeading,
} from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";
import { SeoJsonLd } from "@/components/seo-jsonld";
import { mergeSeoMetadata } from "@/lib/seo-metadata";

export const dynamic = "force-static";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const api = createApiClient();
  const [article, seo] = await Promise.all([
    api.content.getArticle(slug),
    api.seo.getMetadata(`/articles/${slug}`),
  ]);
  return mergeSeoMetadata(seo, {
    title: article?.title ?? "Article",
    description: article?.excerpt,
    alternates: { canonical: `/articles/${slug}` },
  });
}

export default async function ArticlePage({ params }: PageProps) {
  const { slug } = await params;
  const api = createApiClient();
  const [article, related, products] = await Promise.all([
    api.content.getArticle(slug),
    api.content.listArticles(),
    api.affiliate.listProducts(),
  ]);

  if (!article) notFound();
  const seo = await api.seo.getMetadata(`/articles/${slug}`);

  const relatedArticles = related.filter((item) => item.slug !== article.slug).slice(0, 3);
  const affiliatePicks = products.slice(0, 2);

  return (
    <Container className="py-8 sm:py-12">
      <SeoJsonLd seo={seo} />
      <Breadcrumbs
        className="mb-6"
        items={[
          { label: "Home", href: "/" },
          { label: article.category, href: article.categoryHref },
          { label: article.title },
        ]}
      />
      <div className="grid gap-10 lg:grid-cols-12">
        <article className="lg:col-span-8">
          <header>
            <div className="flex flex-wrap items-center gap-2">
              {article.tags.map((tag) => (
                <Badge key={tag}>{tag}</Badge>
              ))}
            </div>
            <h1 className="mt-4 text-3xl font-bold tracking-tight text-text-900 sm:text-4xl">
              {article.title}
            </h1>
            <p className="mt-3 text-sm text-text-600">
              {article.category} · {article.readTime} · Published {article.publishedAt}
            </p>
          </header>
          <div
            aria-hidden="true"
            className="mt-8 flex aspect-[16/9] items-center justify-center rounded-xl border border-border bg-surface-2 text-text-400"
          >
            Featured image placeholder
          </div>
          <DisclosureBadge className="mt-6" />
          <Prose className="mt-8">
            {article.body.map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </Prose>
          <SectionHeading
            level={2}
            className="mt-12"
            title="Related articles"
            description="Continue exploring the same topic."
          />
          <div className="grid gap-6 sm:grid-cols-2">
            {relatedArticles.map((item) => (
              <ContentCard
                key={item.slug}
                title={item.title}
                description={item.excerpt}
                meta={item.readTime}
                href={`/articles/${item.slug}`}
              />
            ))}
          </div>
        </article>

        <aside className="space-y-6 lg:col-span-4">
          <Card title="Table of contents">
            <ul className="space-y-2 text-sm">
              {article.body.map((paragraph, index) => (
                <li key={index} className="text-text-600">
                  Section {index + 1}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Our affiliate picks" description="Tested recommendations from this guide.">
            <div className="space-y-4">
              {affiliatePicks.map((product) => (
                <ContentCard
                  key={product.slug}
                  title={product.name}
                  description={product.summary}
                  meta={product.price}
                  href={`/products/${product.slug}`}
                  badge={<Badge variant="accent">Sponsored</Badge>}
                />
              ))}
            </div>
            <DisclosureBadge className="mt-4" />
          </Card>
        </aside>
      </div>
    </Container>
  );
}
