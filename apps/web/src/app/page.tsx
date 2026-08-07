import type { Metadata } from "next";
import {
  Badge,
  Container,
  ContentCard,
  Hero,
  NewsletterStrip,
  SectionHeading,
} from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: SITE.tagline,
  description: SITE.tagline,
};

export default async function HomePage() {
  const api = createApiClient();
  const [articles, collections, pins] = await Promise.all([
    api.content.listArticles(),
    api.affiliate.listCollections(),
    api.pinterest.listRecentPins(),
  ]);

  return (
    <>
      <Hero
        eyebrow="Product discovery, done properly"
        title="Products worth knowing."
        description="Independent guides and tested recommendations from AtozProductHub — with clear disclosure on every monetized page."
        primaryCta={{ label: "Explore articles", href: "/articles/sample-article" }}
        secondaryCta={{ label: "Browse collections", href: "/collections/sample-collection" }}
      />

      <Container className="py-12 sm:py-16">
        <SectionHeading
          level={2}
          eyebrow="Guides"
          title="Popular articles"
          description="Research you can actually use, written plainly and honestly."
        />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <ContentCard
              key={article.slug}
              title={article.title}
              description={article.excerpt}
              meta={`${article.category} · ${article.readTime}`}
              href={`/articles/${article.slug}`}
            />
          ))}
        </div>
      </Container>

      <Container className="pb-12 sm:pb-16">
        <SectionHeading
          level={2}
          eyebrow="Roundups"
          title="Featured collections"
          description="Curated, compared, and updated — our best lists for high-intent research."
        />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {collections.map((collection) => (
            <ContentCard
              key={collection.slug}
              title={collection.title}
              description={collection.description}
              meta={`${collection.productCount} products compared`}
              href={`/collections/${collection.slug}`}
              badge={<Badge variant="accent">Affiliate</Badge>}
            />
          ))}
        </div>
      </Container>

      <Container className="pb-12 sm:pb-16">
        <SectionHeading
          level={2}
          eyebrow="From Pinterest"
          title="Latest pins"
          description="Recent pin destinations — landing pages that match what you saved."
        />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {pins.map((pin) => (
            <ContentCard
              key={pin.slug}
              title={pin.title}
              meta={`${pin.board} · ${pin.saves} saves`}
              href={`/landing/${pin.slug}`}
              badge={<Badge variant="danger">Pinterest</Badge>}
            />
          ))}
        </div>
      </Container>

      <NewsletterStrip />
    </>
  );
}
