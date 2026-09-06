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

      {products.length > 0 ? (
        <>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {products.map((product, index) => (
              <ContentCard
                key={product.slug}
                title={product.name}
                description={product.summary}
                meta={`${product.price}${product.rating !== undefined ? ` · ★ ${product.rating.toFixed(1)}` : ""}`}
                href={`/products/${product.slug}`}
                badge={<Badge variant="accent">#{String(index + 1).padStart(2, "0")}</Badge>}
              />
            ))}
          </div>
          <p className="mt-4 text-xs text-text-500">
            The connected catalog currently exposes products at the catalog level; collection membership is shown only when supplied by the affiliate service.
          </p>
        </>
      ) : (
        <div className="rounded-2xl border border-border bg-surface-1 p-10 text-center">
          <h2 className="font-serif text-2xl font-bold text-text-900">No products in this catalog yet</h2>
          <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-text-600">
            Products will appear when the connected affiliate catalog publishes inventory for this collection.
          </p>
        </div>
      )}

      <Card className="mt-12" title="How we choose">
        <p className="max-w-2xl text-sm leading-relaxed text-text-600">
          We organize products around the information available from the connected catalog. Pricing, merchant links, and commercial relationships are surfaced where the source data provides them; we do not present unsupported testing or performance claims.
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
                meta={`${item.productCount} products`}
                href={`/collections/${item.slug}`}
              />
            ))}
          </div>
        </>
      )}
    </Container>
  );
}
