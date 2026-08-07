import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
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
  const tag = await createApiClient().content
    .listTags()
    .then((items) => items.find((item) => item.slug === slug));
  return { title: `Tag: ${tag?.name ?? slug}` };
}

export default async function TagPage({ params }: PageProps) {
  const { slug } = await params;
  const api = createApiClient();
  const [tags, articles] = await Promise.all([
    api.content.listTags(),
    api.content.listArticles(),
  ]);
  const tag = tags.find((item) => item.slug === slug);
  if (!tag) notFound();

  const filtered = articles.filter((article) => article.tags.includes(tag.slug));

  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs
        className="mb-6"
        items={[{ label: "Home", href: "/" }, { label: "Tags" }, { label: tag.name }]}
      />
      <SectionHeading
        eyebrow="Tag"
        title={`#${tag.name}`}
        description={`Articles tagged ${tag.name}.`}
      />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((article) => (
          <ContentCard
            key={article.slug}
            title={article.title}
            description={article.excerpt}
            meta={article.readTime}
            href={`/articles/${article.slug}`}
          />
        ))}
      </div>
      <Pagination className="mt-10" page={1} totalPages={1} onPageChange={() => undefined} />
    </Container>
  );
}
