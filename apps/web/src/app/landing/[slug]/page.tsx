import type { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  Badge,
  Breadcrumbs,
  Button,
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
  const landing = await createApiClient().pinterest.getLandingPage(slug);
  return { title: landing?.title ?? "Pinterest landing", description: landing?.intro };
}

export default async function PinterestLandingPage({ params }: PageProps) {
  const { slug } = await params;
  const api = createApiClient();
  const [landingPage, pins, articles] = await Promise.all([
    api.pinterest.getLandingPage(slug),
    api.pinterest.listRecentPins(),
    api.content.listArticles(),
  ]);

  // Wireframe fallback: any pin can be a landing entry point, so unknown
  // slugs render a pin-derived page instead of 404ing (real per-account
  // landing pages arrive with the Pinterest milestone).
  const landing =
    landingPage ??
    (() => {
      const pin = pins.find((item) => item.slug === slug);
      if (!pin) return null;
      return {
        title: pin.title,
        intro:
          "You saved a pin — here is the full guide behind it. This landing page matches the pin promise (wireframe content).",
        articles,
        pins,
      };
    })();
  if (!landing) notFound();

  const relatedPins = pins.filter((pin) => pin.slug !== slug).slice(0, 3);

  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs
        className="mb-6"
        items={[
          { label: "Home", href: "/" },
          { label: "Pinterest", href: "/landing/kitchen-buys" },
          { label: landing.title },
        ]}
      />
      <section className="grid gap-8 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <div
            aria-hidden="true"
            className="flex aspect-[3/4] items-center justify-center rounded-xl border border-border bg-surface-2 text-text-400"
          >
            Pin image placeholder
          </div>
        </div>
        <div className="lg:col-span-7">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="danger">Pinterest</Badge>
            <Badge variant="neutral">Landing page</Badge>
          </div>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-text-900">
            {landing.title}
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-text-600">{landing.intro}</p>
          <DisclosureBadge className="mt-6 max-w-2xl" />
          <div className="mt-6">
            <Button asChild size="lg">
              <a href="/search">Explore the full guide</a>
            </Button>
          </div>
        </div>
      </section>

      <SectionHeading
        level={2}
        className="mt-14"
        eyebrow="From the pin"
        title="Related articles"
        description="The guides behind this pin, in reading order."
      />
      <div className="grid gap-6 sm:grid-cols-2">
        {landing.articles.map((article) => (
          <ContentCard
            key={article.slug}
            title={article.title}
            description={article.excerpt}
            meta={`${article.readTime} · ${article.category}`}
            href={`/articles/${article.slug}`}
          />
        ))}
      </div>

      <SectionHeading level={2} className="mt-14" title="More from Pinterest" description="Keep exploring." />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {relatedPins.map((pin) => (
          <ContentCard
            key={pin.slug}
            title={pin.title}
            meta={`${pin.board} · ${pin.saves} saves`}
            href={`/landing/${pin.slug}`}
          />
        ))}
      </div>
    </Container>
  );
}
