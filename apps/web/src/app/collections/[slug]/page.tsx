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
  const [collection, collections] = await Promise.all([
    api.affiliate.getCollection(slug),
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
          { label: "Collections", href: "/collections" },
          { label: collection.title },
        ]}
      />
      <SectionHeading
        eyebrow="Product collection"
        title={collection.title}
        description={collection.description}
      />
      <DisclosureBadge className="mb-8" />

      <div className="rounded-2xl border border-border bg-surface-1 p-8 sm:p-10">
        <h2 className="font-serif text-2xl font-bold text-text-900">Collection products are not yet exposed</h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-text-600">
          The connected affiliate API currently exposes collection metadata separately from product membership. This page will list products when the source service provides an explicit collection-to-product relationship; it will not guess or mix catalog items into a collection.
        </p>
      </div>

      <Card className="mt-12" title="How we choose">
        <p className="max-w-2xl text-sm leading-relaxed text-text-600">
          We organize products around information supplied by the connected catalog. Pricing, merchant links, and commercial relationships are surfaced where the source data provides them; unsupported testing, performance, or membership claims are not presented.
        </p>
      </Card>

      {relatedCollections.length > 0 && (
        <>
          <SectionHeading level={2} className="mt-14" title="Related collections" />
          <div className="grid gap-6 sm:grid-cols-2">
            {relatedCollections.map((item) => (
              <ContentCard
                key={item.slug}
                title={item.title}
                description={item.description}
                meta={item.productCount > 0 ? `${item.productCount} products` : "Catalog collection"}
                href={`/collections/${item.slug}`}
                badge={<Badge variant="accent">Collection</Badge>}
              />
            ))}
          </div>
        </>
      )}
    </Container>
  );
}
