import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Badge, Breadcrumbs, Container, ContentCard, SectionHeading } from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Collections",
  description: "Browse organized product collections from the AtoZ Product Hub catalog.",
};

export default async function CollectionsPage() {
  const collections = await createApiClient().affiliate.listCollections();

  return (
    <div className="py-8 sm:py-16">
      <Container>
        <Breadcrumbs className="mb-8" items={[{ label: "Home", href: "/" }, { label: "Collections" }]} />
        <div className="max-w-3xl">
          <SectionHeading
            eyebrow="Product Collections"
            title="Browse Collections"
            description="Explore focused product groups organized around practical shopping needs."
          />
        </div>

        {collections.length > 0 ? (
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {collections.map((collection) => (
              <ContentCard
                key={collection.slug}
                title={collection.title}
                description={collection.description}
                meta={`${collection.productCount} products`}
                href={`/collections/${collection.slug}`}
                badge={<Badge variant="accent">Collection</Badge>}
              />
            ))}
          </div>
        ) : (
          <div className="mt-12 rounded-2xl border border-border bg-surface-1 p-10 text-center">
            <h2 className="font-serif text-2xl font-bold text-text-900">No collections are published yet</h2>
            <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-text-600">
              Collections will appear here when the connected product catalog publishes them.
            </p>
            <Link href="/products" className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-primary-600">
              Browse products <ArrowRight className="size-4" />
            </Link>
          </div>
        )}
      </Container>
    </div>
  );
}
