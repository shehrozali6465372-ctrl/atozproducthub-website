import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight, Clock } from "lucide-react";
import { Badge, Breadcrumbs, Container, ContentCard, SectionHeading } from "@atoz/design-system";
import { MOCK_ARTICLES } from "@/lib/mock-data";

export const metadata: Metadata = {
  title: "Editorial Articles & Guides",
  description: "Browse all curated buying guides, masterclasses, and product breakdowns across our 10 niches.",
};

export default function ArticlesPage() {
  const featuredArticle = MOCK_ARTICLES[0];
  const remainingArticles = MOCK_ARTICLES.slice(1);

  return (
    <div className="py-8 sm:py-16">
      <Container>
        <Breadcrumbs className="mb-8" items={[{ label: "Home", href: "/" }, { label: "Articles" }]} />

        <div className="max-w-3xl">
          <SectionHeading
            eyebrow="Editorial Library"
            title="Articles & In-Depth Guides"
            description="Deep, honest breakdowns of tools, essentials, and practices worth bringing into your life."
          />
        </div>

        {/* Featured Editorial Spotlight */}
        {featuredArticle ? (
          <div className="mt-12 overflow-hidden rounded-3xl border border-border/80 bg-surface-0 shadow-sm transition-all duration-300 hover:shadow-xl lg:grid lg:grid-cols-12">
            <div className="relative aspect-[16/10] lg:col-span-7 lg:aspect-auto">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={featuredArticle.image}
                alt={featuredArticle.title}
                className="size-full object-cover"
              />
              <div className="absolute top-4 left-4">
                <Badge variant="accent">Featured Cover Story</Badge>
              </div>
            </div>
            <div className="flex flex-col justify-between p-6 sm:p-10 lg:col-span-5">
              <div>
                <div className="flex items-center gap-3 text-xs font-semibold text-text-400">
                  <span className="uppercase tracking-widest text-primary-500">{featuredArticle.category}</span>
                  <span>·</span>
                  <span className="flex items-center gap-1"><Clock className="size-3.5" /> {featuredArticle.readTime}</span>
                </div>
                <h2 className="mt-4 font-serif text-2xl sm:text-3xl lg:text-4xl font-bold leading-tight text-text-900">
                  <Link href={`/articles/${featuredArticle.slug}`} className="hover:text-primary-500 transition-colors">
                    {featuredArticle.title}
                  </Link>
                </h2>
                <p className="mt-4 text-sm sm:text-base leading-relaxed text-text-600">
                  {featuredArticle.excerpt}
                </p>
              </div>

              <div className="mt-8 flex items-center justify-between border-t border-border/60 pt-6">
                <span className="text-xs text-text-400">Published {featuredArticle.publishedAt}</span>
                <Link
                  href={`/articles/${featuredArticle.slug}`}
                  className="inline-flex items-center gap-2 rounded-full bg-text-900 px-6 py-2.5 text-xs font-bold uppercase tracking-wider text-surface-0 transition-all hover:bg-text-600"
                >
                  <span>Read Guide</span>
                  <ArrowUpRight className="size-4" />
                </Link>
              </div>
            </div>
          </div>
        ) : null}

        {/* All Articles Grid */}
        <div className="mt-16">
          <div className="flex items-center justify-between border-b border-border/60 pb-4">
            <h3 className="font-serif text-2xl font-bold text-text-900">All Published Guides</h3>
            <span className="text-xs font-semibold uppercase tracking-wider text-text-400">
              {MOCK_ARTICLES.length} Articles Total
            </span>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {remainingArticles.map((article) => (
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
        </div>
      </Container>
    </div>
  );
}
