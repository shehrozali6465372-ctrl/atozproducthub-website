"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  Compass,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
} from "lucide-react";
import { Badge, Container, ContentCard } from "@atoz/design-system";
import { NICHES } from "@/lib/niches";
import { MOCK_ARTICLES, MOCK_PRODUCTS } from "@/lib/mock-data";

const TRENDING_SEARCHES = [
  "Minimalist Lighting",
  "Capsule Wardrobe",
  "Skin Barrier Repair",
  "Longevity Mobility",
  "Deep Work Architecture",
];

const TRUST_PILLARS = [
  {
    icon: Compass,
    title: "10 Dedicated Universes",
    description: "Completely isolated niche hubs. Zero cross-category distraction or clutter.",
  },
  {
    icon: Sparkles,
    title: "8K Tested Standard",
    description: "Every guide and item is hand-evaluated for real craftsmanship, durability, and utility.",
  },
  {
    icon: ShieldCheck,
    title: "Absolute Editorial Truth",
    description: "Transparent disclosures with zero simulated or fake metrics. Pure independent curation.",
  },
];

const NICHE_CLUSTERS = [
  { label: "All 10 Worlds", filter: "all" },
  { label: "Living & Design", filter: "living" },
  { label: "Style & Beauty", filter: "style" },
  { label: "Health & Mindset", filter: "health" },
  { label: "Family & Craft", filter: "craft" },
];

export default function HomePage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCluster, setActiveCluster] = useState("all");
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newsletterEmail.trim()) {
      setSubscribed(true);
    }
  };

  const filteredNiches = NICHES.filter((niche) => {
    if (activeCluster === "all") return true;
    if (activeCluster === "living") {
      return ["home-decor", "food-recipes"].includes(niche.slug);
    }
    if (activeCluster === "style") {
      return ["fashion", "beauty-skincare", "wedding-planning"].includes(niche.slug);
    }
    if (activeCluster === "health") {
      return ["health-wellness", "productivity", "personal-finance"].includes(niche.slug);
    }
    if (activeCluster === "craft") {
      return ["diy-crafts", "parenting-kids"].includes(niche.slug);
    }
    return true;
  });

  const featuredArticles = MOCK_ARTICLES.slice(0, 3);
  const featuredProducts = MOCK_PRODUCTS.slice(0, 4);

  return (
    <div className="relative overflow-hidden">
      {/* ========================================================================= */}
      {/* 1. HERO SECTION — Ultra-Luxury Editorial Banner                           */}
      {/* ========================================================================= */}
      <section className="relative pt-12 pb-20 sm:pt-20 sm:pb-28 lg:pt-28 lg:pb-32">
        {/* Optical Ambient Lighting */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 -top-40 -z-10 flex transform-gpu justify-center overflow-hidden blur-3xl"
        >
          <div className="aspect-[1155/678] w-[72rem] bg-gradient-to-tr from-amber-500/10 via-primary-500/10 to-indigo-500/10 opacity-70 dark:opacity-30" />
        </div>

        <Container className="text-center">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-surface-1/90 px-4 py-1.5 backdrop-blur-md shadow-2xs">
            <span className="size-2 rounded-full bg-primary-500 animate-pulse" />
            <span className="text-[11px] font-bold uppercase tracking-[0.22em] text-text-700">
              The Curated Discovery Network · 10 Niches
            </span>
          </div>

          {/* Luxury Display Typography */}
          <h1 className="mx-auto mt-8 max-w-5xl font-serif text-4xl font-bold leading-[1.08] tracking-tight text-text-900 sm:text-6xl md:text-7xl lg:text-[84px]">
            Discover Your World.
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-text-600 sm:text-lg md:text-xl font-normal text-balance">
            Explore carefully curated ideas, tested products and editorial inspiration across{" "}
            <span className="font-semibold text-text-900">10 specialized niches</span>.
          </p>

          {/* Interactive Hero Search Form */}
          <form
            onSubmit={handleSearchSubmit}
            className="mx-auto mt-10 max-w-2xl rounded-2xl border border-border/80 bg-surface-0/90 p-2 shadow-lg backdrop-blur-md transition-all focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20"
          >
            <div className="flex items-center gap-2">
              <div className="grid size-11 place-items-center rounded-xl bg-surface-1 text-text-400">
                <Search className="size-5" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search across all 10 niches, products, and guides..."
                className="w-full bg-transparent text-sm font-medium text-text-900 placeholder:text-text-400 focus:outline-none"
              />
              <button
                type="submit"
                className="inline-flex h-11 items-center rounded-xl bg-text-900 px-6 text-xs font-bold uppercase tracking-wider text-surface-0 transition-all hover:bg-text-600 shrink-0"
              >
                Search
              </button>
            </div>
          </form>

          {/* Quick Search Chips */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-xs">
            <span className="text-text-400 font-semibold uppercase tracking-wider text-[10px]">
              Trending:
            </span>
            {TRENDING_SEARCHES.map((term) => (
              <button
                key={term}
                type="button"
                onClick={() => router.push(`/search?q=${encodeURIComponent(term)}`)}
                className="rounded-full border border-border/60 bg-surface-1/50 px-3 py-1 text-text-600 transition-all hover:border-primary-500/50 hover:bg-surface-0 hover:text-text-900"
              >
                {term}
              </button>
            ))}
          </div>

          {/* Dual Main CTAs */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <a
              href="#niches"
              className="inline-flex h-13 items-center justify-center rounded-full bg-text-900 px-8 text-xs font-bold uppercase tracking-[0.2em] text-surface-0 shadow-sm transition-all duration-200 hover:bg-text-600 hover:shadow-md dark:bg-surface-0 dark:text-text-900 dark:hover:bg-surface-1"
            >
              <span>Explore Niches</span>
              <ArrowRight className="ml-2.5 size-4" aria-hidden="true" />
            </a>
            <Link
              href="/about"
              className="inline-flex h-13 items-center justify-center rounded-full border border-border bg-surface-0/80 px-8 text-xs font-bold uppercase tracking-[0.2em] text-text-900 backdrop-blur-xs transition-all duration-200 hover:bg-surface-1 hover:border-text-400"
            >
              Learn About Us
            </Link>
          </div>
        </Container>
      </section>

      {/* ========================================================================= */}
      {/* 2. STATS & METRICS RIBBON                                                 */}
      {/* ========================================================================= */}
      <section className="border-y border-border/70 bg-surface-1/40 py-8">
        <Container>
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4 text-center">
            <div>
              <div className="font-serif text-3xl font-bold text-text-900">10</div>
              <div className="text-xs uppercase tracking-wider text-text-500 mt-1 font-semibold">
                Dedicated Worlds
              </div>
            </div>
            <div>
              <div className="font-serif text-3xl font-bold text-text-900">100%</div>
              <div className="text-xs uppercase tracking-wider text-text-500 mt-1 font-semibold">
                Independent Reviews
              </div>
            </div>
            <div>
              <div className="font-serif text-3xl font-bold text-text-900">8K</div>
              <div className="text-xs uppercase tracking-wider text-text-500 mt-1 font-semibold">
                Editorial Standard
              </div>
            </div>
            <div>
              <div className="font-serif text-3xl font-bold text-text-900">0%</div>
              <div className="text-xs uppercase tracking-wider text-text-500 mt-1 font-semibold">
                Cross-Niche Clutter
              </div>
            </div>
          </div>
        </Container>
      </section>

      {/* ========================================================================= */}
      {/* 3. 10-NICHE GATEWAY — Non-Negotiable 10 Worlds with Cluster Filtering     */}
      {/* ========================================================================= */}
      <section id="niches" className="scroll-mt-20 py-20 sm:py-28">
        <Container>
          {/* Section Header with Category Tabs */}
          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end border-b border-border/60 pb-8">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-[0.22em] text-primary-500">
                10 Independent Universes
              </span>
              <h2 className="mt-2 font-serif text-3xl font-bold tracking-tight text-text-900 sm:text-4xl lg:text-5xl">
                Explore Our Niches
              </h2>
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap gap-2">
              {NICHE_CLUSTERS.map((cluster) => (
                <button
                  key={cluster.filter}
                  onClick={() => setActiveCluster(cluster.filter)}
                  className={`rounded-full px-4 py-1.5 text-xs font-bold uppercase tracking-wider transition-all ${
                    activeCluster === cluster.filter
                      ? "bg-text-900 text-surface-0 shadow-xs"
                      : "border border-border/70 bg-surface-0 text-text-600 hover:bg-surface-1 hover:text-text-900"
                  }`}
                >
                  {cluster.label}
                </button>
              ))}
            </div>
          </div>

          {/* 10 Niche Cards Grid: 5x2 on desktop, 3 cols on tablet, 1 col on mobile */}
          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
            {filteredNiches.map((niche, index) => (
              <Link
                key={niche.slug}
                href={`/categories/${niche.slug}`}
                className="group relative flex flex-col overflow-hidden rounded-2xl border border-border/70 bg-surface-0 p-3 shadow-2xs transition-all duration-300 hover:-translate-y-1.5 hover:border-primary-500/60 hover:shadow-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
              >
                {/* Visual Imagery */}
                <div className="relative aspect-[4/5] w-full overflow-hidden rounded-xl bg-surface-2">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={niche.image}
                    alt={niche.name}
                    loading="lazy"
                    decoding="async"
                    className="size-full object-cover transition-transform duration-700 ease-out group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/15 to-transparent opacity-70 transition-opacity duration-300 group-hover:opacity-40" />

                  {/* Niche Order Badge */}
                  <div className="absolute top-3 left-3 rounded-full bg-black/50 px-2.5 py-0.5 text-[10px] font-bold tracking-widest text-white/90 backdrop-blur-md">
                    0{index + 1}
                  </div>
                  <div className="absolute bottom-3 left-3 right-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-300">
                      {niche.shortName}
                    </span>
                  </div>
                </div>

                {/* Content Details */}
                <div className="flex flex-1 flex-col justify-between p-3 pt-4">
                  <div>
                    <h3 className="font-serif text-lg font-bold leading-snug tracking-tight text-text-900 transition-colors group-hover:text-primary-500">
                      {niche.name}
                    </h3>
                    <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-text-600">
                      {niche.description}
                    </p>
                  </div>

                  {/* Action Link */}
                  <div className="mt-5 flex items-center justify-between border-t border-border/40 pt-3 text-[11px] font-bold uppercase tracking-[0.16em] text-text-400 transition-colors group-hover:text-text-900">
                    <span>Enter World</span>
                    <ArrowRight
                      aria-hidden="true"
                      className="size-3.5 transition-transform duration-200 group-hover:translate-x-1"
                    />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </Container>
      </section>

      {/* ========================================================================= */}
      {/* 4. FEATURED EDITORIAL STORIES & MASTERCLASSES                             */}
      {/* ========================================================================= */}
      <section className="border-t border-border/70 bg-surface-1/30 py-20 sm:py-28">
        <Container>
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end border-b border-border/60 pb-8">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-[0.22em] text-primary-500">
                Editorial Curations
              </span>
              <h2 className="mt-2 font-serif text-3xl font-bold tracking-tight text-text-900 sm:text-4xl lg:text-5xl">
                Featured Guides & Stories
              </h2>
            </div>
            <Link
              href="/articles"
              className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-text-900 hover:text-primary-500 transition-colors"
            >
              <span>View All Articles</span>
              <ArrowRight className="size-4" />
            </Link>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            {featuredArticles.map((article) => (
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
        </Container>
      </section>

      {/* ========================================================================= */}
      {/* 5. CURATED GEAR & TESTED PRODUCTS SHOWCASE                                */}
      {/* ========================================================================= */}
      <section className="border-t border-border/70 bg-surface-0 py-20 sm:py-28">
        <Container>
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end border-b border-border/60 pb-8">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-[0.22em] text-primary-500">
                Hand-Selected Essentials
              </span>
              <h2 className="mt-2 font-serif text-3xl font-bold tracking-tight text-text-900 sm:text-4xl lg:text-5xl">
                Trending Tested Gear
              </h2>
            </div>
            <Link
              href="/products"
              className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-text-900 hover:text-primary-500 transition-colors"
            >
              <span>Explore All Products</span>
              <ArrowRight className="size-4" />
            </Link>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {featuredProducts.map((prod) => (
              <div
                key={prod.slug}
                className="group flex flex-col justify-between overflow-hidden rounded-2xl border border-border/70 bg-surface-0 p-3 shadow-2xs transition-all duration-300 hover:-translate-y-1 hover:border-primary-500/50 hover:shadow-lg"
              >
                <div>
                  <div className="relative aspect-square w-full overflow-hidden rounded-xl bg-surface-2">
                    {prod.image ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={prod.image}
                        alt={prod.name}
                        loading="lazy"
                        className="size-full object-cover transition-transform duration-500 ease-out group-hover:scale-105"
                      />
                    ) : null}
                    <div className="absolute top-2.5 right-2.5">
                      <span className="inline-flex items-center gap-1 rounded-full bg-black/60 px-2 py-0.5 text-[11px] font-bold text-amber-300 backdrop-blur-md">
                        <Star className="size-3 fill-amber-300 text-amber-300" />
                        {prod.rating}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 p-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-text-900">{prod.price}</span>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-primary-500">
                        Tested
                      </span>
                    </div>
                    <h3 className="mt-1.5 font-serif text-base font-bold text-text-900 leading-snug group-hover:text-primary-500 transition-colors">
                      <Link href={`/products/${prod.slug}`}>
                        {prod.name}
                      </Link>
                    </h3>
                    <p className="mt-2 text-xs leading-relaxed text-text-600 line-clamp-2">
                      {prod.summary}
                    </p>
                  </div>
                </div>

                <div className="mt-4 border-t border-border/40 p-1 pt-3 flex items-center justify-between">
                  <Link
                    href={`/products/${prod.slug}`}
                    className="text-[11px] font-bold uppercase tracking-wider text-text-400 hover:text-text-900"
                  >
                    Specs & Pros
                  </Link>
                  <Link
                    href={`/products/${prod.slug}`}
                    className="inline-flex items-center gap-1 rounded-full bg-surface-1 px-3 py-1 text-xs font-bold uppercase tracking-wider text-text-900 transition-all hover:bg-text-900 hover:text-surface-0"
                  >
                    <span>Review</span>
                    <ArrowUpRight className="size-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </Container>
      </section>

      {/* ========================================================================= */}
      {/* 6. VIP NEWSLETTER & CURATION STRIP                                        */}
      {/* ========================================================================= */}
      <section className="border-t border-border/70 bg-surface-1/40 py-20 sm:py-24">
        <Container>
          <div className="relative overflow-hidden rounded-3xl border border-border/80 bg-gradient-to-br from-surface-0 via-surface-1 to-surface-0 p-8 sm:p-14 shadow-lg">
            <div className="max-w-2xl">
              <span className="text-[11px] font-bold uppercase tracking-[0.22em] text-primary-500">
                The Weekly Digest
              </span>
              <h2 className="mt-3 font-serif text-3xl sm:text-4xl lg:text-5xl font-bold text-text-900">
                Fewer, Better Things In Your Inbox.
              </h2>
              <p className="mt-4 text-sm sm:text-base leading-relaxed text-text-600">
                Join 45,000+ tastemakers who receive our weekly curated dispatch spanning interior design, culinary tools, capsule style, and deep productivity.
              </p>

              {subscribed ? (
                <div className="mt-8 flex items-center gap-3 rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-emerald-700 dark:text-emerald-300">
                  <CheckCircle2 className="size-5" />
                  <span className="text-sm font-semibold">
                    Thank you! You are now subscribed to the AtoZ Product Hub Weekly Digest.
                  </span>
                </div>
              ) : (
                <form onSubmit={handleNewsletterSubmit} className="mt-8 flex flex-col sm:flex-row gap-3">
                  <input
                    type="email"
                    required
                    value={newsletterEmail}
                    onChange={(e) => setNewsletterEmail(e.target.value)}
                    placeholder="Enter your email address..."
                    className="h-12 w-full rounded-full border border-border/80 bg-surface-0 px-5 text-sm font-medium text-text-900 placeholder:text-text-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 sm:max-w-md"
                  />
                  <button
                    type="submit"
                    className="inline-flex h-12 items-center justify-center rounded-full bg-text-900 px-8 text-xs font-bold uppercase tracking-[0.2em] text-surface-0 transition-all hover:bg-text-600 shrink-0 shadow-sm"
                  >
                    Subscribe
                  </button>
                </form>
              )}

              <p className="mt-4 text-[11px] text-text-400">
                Zero spam. Completely free. Unsubscribe with one click anytime.
              </p>
            </div>
          </div>
        </Container>
      </section>

      {/* ========================================================================= */}
      {/* 7. VALUE & TRUST STRIP                                                    */}
      {/* ========================================================================= */}
      <section className="border-t border-border/70 bg-surface-0 py-16 sm:py-20">
        <Container>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {TRUST_PILLARS.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.title}
                  className="flex items-start gap-4 rounded-2xl border border-border/60 bg-surface-1/40 p-6 shadow-2xs"
                >
                  <div className="grid size-12 shrink-0 place-items-center rounded-xl bg-surface-0 shadow-2xs ring-1 ring-border/60 text-primary-500">
                    <Icon className="size-5" aria-hidden="true" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold tracking-tight text-text-900">
                      {pillar.title}
                    </h4>
                    <p className="mt-1.5 text-xs leading-relaxed text-text-600">
                      {pillar.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </Container>
      </section>
    </div>
  );
}
