import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  Badge,
  Breadcrumbs,
  Button,
  Card,
  Container,
  ContentCard,
  DisclosureBadge,
  SectionHeading,
} from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";
import { AffiliateBuyButton } from "@/components/affiliate-buy-button";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const product = await createApiClient().affiliate.getProduct(slug);
  return { title: product?.name ?? "Product", description: product?.summary };
}

export default async function ProductPage({ params }: PageProps) {
  const { slug } = await params;
  const api = createApiClient();
  const [product, related] = await Promise.all([
    api.affiliate.getProduct(slug),
    api.affiliate.listProducts(),
  ]);
  if (!product) notFound();

  const relatedProducts = related.filter((item) => item.slug !== product.slug).slice(0, 3);

  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs
        className="mb-6"
        items={[
          { label: "Home", href: "/" },
          { label: "Products", href: "/products/sample-product" },
          { label: product.name },
        ]}
      />
      <div className="grid gap-10 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <div
            aria-hidden="true"
            className="flex aspect-square max-w-xl items-center justify-center rounded-xl border border-border bg-surface-2 text-text-400"
          >
            Gallery placeholder
          </div>
          <div className="mt-4 flex gap-2">
            {["Angle 1", "Angle 2", "Angle 3"].map((label) => (
              <span
                key={label}
                className="grid h-16 w-16 place-items-center rounded-lg border border-border bg-surface-1 text-[10px] text-text-400"
              >
                {label}
              </span>
            ))}
          </div>
        </div>
        <div className="lg:col-span-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="accent">Affiliate product</Badge>
            {product.rating !== undefined && (
              <Badge variant="neutral">★ {product.rating.toFixed(1)} / 5</Badge>
            )}
          </div>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-text-900">
            {product.name}
          </h1>
          <p className="mt-2 font-mono text-2xl font-semibold text-text-900">
            {product.price}
          </p>
          <p className="mt-4 text-text-600">{product.summary}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            {product.buyUrl ? (
              <AffiliateBuyButton goUrl={product.buyUrl} />
            ) : (
              <Button asChild size="lg">
                <a href="#" rel="sponsored nofollow">
                  Buy now
                </a>
              </Button>
            )}
            <Button asChild variant="outline" size="lg">
              <a href={`/collections/sample-collection`}>View collection</a>
            </Button>
          </div>
          {product.disclosureRequired !== false && <DisclosureBadge className="mt-6" />}
          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            {product.pros !== undefined && (
              <Card title="Pros">
                <ul className="space-y-2 text-sm text-text-600">
                  {product.pros.map((pro) => (
                    <li key={pro} className="flex gap-2">
                      <span aria-hidden="true" className="text-success-500">
                        +
                      </span>
                      {pro}
                    </li>
                  ))}
                </ul>
              </Card>
            )}
            {product.cons !== undefined && (
              <Card title="Cons">
                <ul className="space-y-2 text-sm text-text-600">
                  {product.cons.map((con) => (
                    <li key={con} className="flex gap-2">
                      <span aria-hidden="true" className="text-danger-500">
                        −
                      </span>
                      {con}
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
          <Card className="mt-6" title="Frequently asked questions">
            <div className="space-y-3">
              {[
                ["Is this product tested?", "Yes — the recommendation process is documented in our methodology."],
                ["What is the return policy?", "Returns follow the retailer's policy; links are clearly disclosed."],
              ].map(([question, answer]) => (
                <details key={question} className="rounded-lg border border-border bg-surface-0 p-3 text-sm">
                  <summary className="cursor-pointer font-medium text-text-900">{question}</summary>
                  <p className="mt-2 text-text-600">{answer}</p>
                </details>
              ))}
            </div>
          </Card>
        </div>
      </div>

      <SectionHeading level={2} className="mt-14" title="Related products" description="Compare before you buy." />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {relatedProducts.map((item) => (
          <ContentCard
            key={item.slug}
            title={item.name}
            description={item.summary}
            meta={item.price}
            href={`/products/${item.slug}`}
          />
        ))}
      </div>
    </Container>
  );
}
