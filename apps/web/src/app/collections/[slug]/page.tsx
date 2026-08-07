import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  Badge,
  Breadcrumbs,
  Card,
  Container,
  ContentCard,
  DisclosureBadge,
  SectionHeading,
} from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const collection = await createApiClient().affiliate.getCollection(slug);
  return {
    title: collection?.title ?? "Collection",
    description: collection?.description,
  };
}

export default async function AffiliateCollectionPage({ params }: PageProps) {
  const { slug } = await params;
  const api = createApiClient();
  const [collection, products, collections] = await Promise.all([
    api.affiliate.getCollection(slug),
    api.affiliate.listProducts(),
    api.affiliate.listCollections(),
  ]);
  if (!collection) notFound();

  const relatedCollections = collections.filter((item) => item.slug !== collection.slug).slice(0, 2);

  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs
        className="mb-6"
        items={[
          { label: "Home", href: "/" },
          { label: "Collections", href: "/collections/sample-collection" },
          { label: collection.title },
        ]}
      />
      <SectionHeading
        eyebrow="Affiliate collection"
        title={collection.title}
        description={collection.description}
        action={<Badge variant="accent">Updated 2026</Badge>}
      />
      <DisclosureBadge className="mb-8" />

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((product, index) => (
          <ContentCard
            key={product.slug}
            title={`${index + 1}. ${product.name}`}
            description={product.summary}
            meta={`${product.price} · ★ ${product.rating.toFixed(1)}`}
            href={`/products/${product.slug}`}
            badge={<Badge variant="accent">#{(index + 1).toString().padStart(2, "0")}</Badge>}
          />
        ))}
      </div>

      <Card className="mt-12" title="How we choose">
        <p className="max-w-2xl text-sm leading-relaxed text-text-600">
          Every product in this roundup is tested against the same criteria:
          does it solve a real problem, is it well built, and does the price
          match the value? Full methodology and disclosure live on the
          disclaimer page.
        </p>
      </Card>

      <SectionHeading level={2} className="mt-14" title="Related collections" />
      <div className="grid gap-6 sm:grid-cols-2">
        {relatedCollections.map((item) => (
          <ContentCard
            key={item.slug}
            title={item.title}
            description={item.description}
            meta={`${item.productCount} products compared`}
            href={`/collections/${item.slug}`}
          />
        ))}
      </div>
    </Container>
  );
}
