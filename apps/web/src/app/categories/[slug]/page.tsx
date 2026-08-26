import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowRight, BookOpen, Compass, Sparkles } from "lucide-react";
import {
  Badge,
  Breadcrumbs,
  Container,
  ContentCard,
} from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";
import { NICHES } from "@/lib/niches";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const niche = NICHES.find((n) => n.slug === slug);
  if (niche) {
    return {
      title: `${niche.name} — AtoZ Product Hub`,
      description: niche.description,
    };
  }

  const category = await createApiClient().content
    .listCategories()
    .then((items) => items.find((item) => item.slug === slug));

  return {
    title: `${category?.name ?? "Category"} — AtoZ Product Hub`,
    description: category?.description ?? "Curated guides and product recommendations.",
  };
}

export default async function CategoryPage({ params }: PageProps) {
  const { slug } = await params;
  const api = createApiClient();
  const [categories, articles] = await Promise.all([
    api.content.listCategories(),
    api.content.listArticles(),
  ]);

  const niche = NICHES.find((n) => n.slug === slug);
  const category = categories.find((item) => item.slug === slug);

  if (!niche && !category) notFound();

  const title = niche?.name ?? category?.name ?? "Niche";
  const description = niche?.description ?? category?.description ?? "";
  const nicheImage = niche?.image ?? "/images/hero/editorial-hero.jpg";

  // Filter articles strictly for this niche/category
  const filteredArticles = articles.filter(
    (article) =>
      article.category.toLowerCase() === title.toLowerCase() ||
      article.category.toLowerCase() === (niche?.shortName ?? "").toLowerCase() ||
      article.tags.some((t) => t.toLowerCase() === slug.toLowerCase()),
  );

  return (
    <div className="relative pb-24">
      {/* Niche World Hero */}
      <section className="relative border-b border-border/70 bg-surface-1/40 pt-10 pb-16 sm:pt-14 sm:pb-20">
        <Container>
          <Breadcrumbs
            className="mb-8"
            items={[
              { label: "Home", href: "/" },
              { label: "Niches", href: "/#niches" },
              { label: title },
            ]}
          />

          <div className="grid items-center gap-10 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-surface-0 px-3.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary-500 shadow-2xs">
                <Compass className="size-3.5" aria-hidden="true" />
                <span>Dedicated Niche Universe</span>
              </div>

              <h1 className="mt-4 font-serif text-3xl font-bold tracking-tight text-text-900 sm:text-5xl lg:text-6xl">
                {title}
              </h1>

              <p className="mt-4 max-w-xl text-base leading-relaxed text-text-600 sm:text-lg">
                {description}
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-4">
                <a
                  href="#articles"
                  className="inline-flex h-11 items-center gap-2 rounded-full bg-text-900 px-6 text-xs font-bold uppercase tracking-[0.16em] text-surface-0 shadow-xs transition-all hover:bg-text-600 dark:bg-surface-0 dark:text-text-900 dark:hover:bg-surface-1"
                >
                  <span>Explore Guides</span>
                  <ArrowRight className="size-3.5" aria-hidden="true" />
                </a>
                <Link
                  href="/#niches"
                  className="inline-flex h-11 items-center gap-2 rounded-full border border-border bg-surface-0 px-5 text-xs font-semibold uppercase tracking-[0.14em] text-text-600 transition-colors hover:bg-surface-1 hover:text-text-900"
                >
                  <ArrowLeft className="size-3.5" aria-hidden="true" />
                  <span>All Niches</span>
                </Link>
              </div>
            </div>

            <div className="lg:col-span-5">
              <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl border border-border/70 bg-surface-2 shadow-sm">
                <Image
                  src={nicheImage}
                  alt={title}
                  fill
                  priority
                  sizes="(max-width: 1024px) 100vw, 40vw"
                  className="object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-60" />
                <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between text-white/90">
                  <span className="text-xs font-semibold tracking-wider uppercase backdrop-blur-md bg-black/40 px-3 py-1 rounded-full">
                    AtoZ Product Hub
                  </span>
                  <Sparkles className="size-4 text-primary-500" aria-hidden="true" />
                </div>
              </div>
            </div>
          </div>
        </Container>
      </section>

      {/* Guides & Content Section */}
      <section id="articles" className="pt-16 sm:pt-20">
        <Container>
          <div className="flex items-center justify-between border-b border-border/60 pb-6">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-text-400">
                Curated Knowledge
              </span>
              <h2 className="mt-1 font-serif text-2xl font-bold tracking-tight text-text-900 sm:text-3xl">
                Guides & Recommendations
              </h2>
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-text-400">
              {filteredArticles.length > 0 ? `${filteredArticles.length} Available` : "Curating Now"}
            </span>
          </div>

          {filteredArticles.length === 0 ? (
            <div className="mt-10 rounded-2xl border border-border/70 bg-surface-1/40 p-10 text-center">
              <BookOpen className="mx-auto size-10 text-text-400" aria-hidden="true" />
              <h3 className="mt-4 font-serif text-xl font-bold text-text-900">
                Fresh Editorial Guides Coming Soon
              </h3>
              <p className="mx-auto mt-2 max-w-md text-sm text-text-600">
                Our editorial team is actively reviewing and testing products in {title}. Check back soon or explore our other specialized niches.
              </p>
              <div className="mt-6">
                <Link
                  href="/#niches"
                  className="inline-flex h-10 items-center rounded-full bg-surface-0 border border-border px-6 text-xs font-bold uppercase tracking-wider text-text-900 hover:bg-surface-2 transition-colors"
                >
                  Browse Other Niches
                </Link>
              </div>
            </div>
          ) : (
            <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {filteredArticles.map((article) => (
                <ContentCard
                  key={article.slug}
                  title={article.title}
                  description={article.excerpt}
                  image={article.image}
                  meta={`${article.readTime} · ${article.publishedAt}`}
                  href={`/articles/${article.slug}`}
                  badge={<Badge variant="neutral">{article.category}</Badge>}
                />
              ))}
            </div>
          )}
        </Container>
      </section>
    </div>
  );
}
