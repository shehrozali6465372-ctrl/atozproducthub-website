"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  ArrowUpRight,
  Bookmark,
  CheckCircle2,
  Compass,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
} from "lucide-react";
import { Badge, Container } from "@atoz/design-system";
import { NICHES } from "@/lib/niches";
import { MOCK_ARTICLES, MOCK_PRODUCTS } from "@/lib/mock-data";

const TRENDING_SEARCHES = [
  "Minimalist Lighting",
  "Capsule Wardrobe",
  "Skin Barrier Repair",
  "Longevity Mobility",
  "Deep Work Architecture",
];

const EDITORIAL_PILLARS = [
  {
    icon: Compass,
    title: "10 Independent Worlds",
    description: "Each niche stays visually and editorially isolated with no cross-category clutter.",
  },
  {
    icon: Sparkles,
    title: "Calm Luxury Language",
    description: "Warm ivory, muted bronze, and restrained typography create an editorial magazine feel.",
  },
  {
    icon: ShieldCheck,
    title: "Trust Over Hype",
    description: "Clear disclosure, honest product framing, and measured calls to action throughout.",
  },
];

const BRAND_NOTES = [
  "Image-first hierarchy",
  "Warm ivory surfaces",
  "Muted bronze accents",
  "Editorial typography",
];

function SectionHeading({
  eyebrow,
  title,
  description,
  align = "left",
}: {
  eyebrow: string;
  title: string;
  description: string;
  align?: "left" | "center";
}) {
  return (
    <div className={align === "center" ? "mx-auto max-w-3xl text-center" : "max-w-3xl"}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-primary-500">
        {eyebrow}
      </p>
      <h2 className="mt-3 font-serif text-3xl font-bold tracking-tight text-text-900 sm:text-4xl lg:text-[3.15rem]">
        {title}
      </h2>
      <p className="mt-4 text-base leading-relaxed text-text-600 sm:text-lg">
        {description}
      </p>
    </div>
  );
}

function MiniMetric({
  value,
  label,
}: {
  value: string;
  label: string;
}) {
  return (
    <div className="rounded-2xl border border-border/80 bg-surface-1/90 p-4 shadow-[0_18px_48px_-40px_rgba(0,0,0,0.4)]">
      <div className="font-serif text-2xl font-bold text-text-900">{value}</div>
      <div className="mt-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-text-400">
        {label}
      </div>
    </div>
  );
}

export default function HomePage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
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

  const featuredArticle = MOCK_ARTICLES[0];
  const featuredStories = MOCK_ARTICLES.slice(0, 4);
  const featuredProducts = MOCK_PRODUCTS.slice(0, 4);
  const pinWorlds = NICHES.slice(0, 6);

  return (
    <div className="relative overflow-hidden">
      <section className="relative isolate overflow-hidden pb-14 pt-10 sm:pb-16 sm:pt-14 lg:pb-24 lg:pt-16">
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-x-0 top-0 h-[34rem] bg-[radial-gradient(circle_at_top,rgba(164,119,82,0.16),transparent_46%),radial-gradient(circle_at_80%_10%,rgba(217,200,181,0.4),transparent_34%)]" />
          <div className="editorial-grid absolute inset-0 opacity-40" />
        </div>

        <Container>
          <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-surface-1/90 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-text-600 shadow-[0_16px_40px_-36px_rgba(0,0,0,0.45)]">
                <span className="size-2 rounded-full bg-primary-500" />
                10 independent content worlds
              </div>

              <h1 className="mt-7 max-w-xl font-serif text-[clamp(2.5rem,6vw,4.9rem)] font-bold leading-[0.94] tracking-tight text-text-900">
                Discover Your World.
              </h1>

              <p className="mt-5 max-w-xl text-lg leading-relaxed text-text-600 sm:text-xl">
                Premium editorial commerce across articles, products, collections, and Pinterest-ready discovery.
                Warm, calm, and curated for readers who want fewer things that matter more.
              </p>

              <form
                onSubmit={handleSearchSubmit}
                className="mt-8 rounded-3xl border border-border/80 bg-surface-1/95 p-2 shadow-[0_28px_60px_-44px_rgba(0,0,0,0.4)] backdrop-blur"
              >
                <div className="flex flex-col gap-3 rounded-2xl bg-surface-0 px-4 py-3 sm:flex-row sm:items-center">
                  <div className="flex items-center gap-3">
                    <div className="grid size-11 place-items-center rounded-2xl bg-text-900 text-surface-0">
                      <Search aria-hidden="true" className="size-4" />
                    </div>
                    <div className="hidden sm:block">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-400">
                        Search the archive
                      </p>
                      <p className="text-sm text-text-600">
                        Articles, products, collections, and worlds
                      </p>
                    </div>
                  </div>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by niche, product, article, or theme..."
                    className="min-w-0 flex-1 bg-transparent text-sm font-medium text-text-900 placeholder:text-text-400 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="inline-flex h-11 items-center justify-center rounded-xl bg-text-900 px-5 text-[11px] font-semibold uppercase tracking-[0.2em] text-surface-0 transition-colors hover:bg-text-600"
                  >
                    Search
                  </button>
                </div>
              </form>

              <div className="mt-5 flex flex-wrap items-center gap-2 text-xs">
                <span className="mr-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-text-400">
                  Trending
                </span>
                {TRENDING_SEARCHES.map((term) => (
                  <button
                    key={term}
                    type="button"
                    onClick={() => router.push(`/search?q=${encodeURIComponent(term)}`)}
                    className="rounded-full border border-border/70 bg-surface-1/90 px-3.5 py-1.5 text-text-600 transition-colors hover:border-primary-500/40 hover:text-text-900"
                  >
                    {term}
                  </button>
                ))}
              </div>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <a
                  href="#worlds"
                  className="inline-flex h-12 items-center justify-center rounded-xl bg-text-900 px-6 text-[12px] font-semibold uppercase tracking-[0.2em] text-surface-0 transition-colors hover:bg-text-600"
                >
                  Explore Worlds
                  <ArrowRight className="ml-2 size-4" />
                </a>
                <Link
                  href="/articles"
                  className="inline-flex h-12 items-center justify-center rounded-xl border border-border/80 bg-surface-1/90 px-6 text-[12px] font-semibold uppercase tracking-[0.2em] text-text-900 transition-colors hover:bg-surface-0"
                >
                  Read Editorials
                </Link>
              </div>

              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                {EDITORIAL_PILLARS.map((pillar) => {
                  const Icon = pillar.icon;
                  return (
                    <div key={pillar.title} className="rounded-2xl border border-border/80 bg-surface-1/85 p-4">
                      <div className="flex items-start gap-3">
                        <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-surface-0 text-primary-500 ring-1 ring-border/70">
                          <Icon aria-hidden="true" className="size-4" />
                        </div>
                        <div>
                          <h2 className="text-sm font-semibold text-text-900">{pillar.title}</h2>
                          <p className="mt-1 text-xs leading-relaxed text-text-600">{pillar.description}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="relative">
              <div className="absolute -left-4 top-10 hidden h-24 w-24 rounded-full border border-border/60 bg-[radial-gradient(circle,rgba(164,119,82,0.18),transparent_70%)] lg:block" />
              <div className="absolute -right-4 bottom-16 hidden h-36 w-36 rounded-full border border-border/50 bg-[radial-gradient(circle,rgba(217,200,181,0.35),transparent_68%)] lg:block" />

              <div className="relative overflow-hidden rounded-[2rem] border border-border/80 bg-surface-1 p-3 shadow-[0_32px_80px_-44px_rgba(0,0,0,0.55)]">
                <div className="grid gap-3 sm:grid-cols-[1.1fr_0.9fr]">
                  <div className="relative aspect-[16/9] sm:aspect-[4/3] overflow-hidden rounded-[1.6rem]">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                  <Image
                      src={featuredArticle.image ?? NICHES[0].image}
                      alt={featuredArticle.title}
                      fill
                      priority
                      sizes="(max-width: 1024px) 100vw, 48vw"
                      className="object-cover"
                    />
                    <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(23,23,23,0.04)_0%,rgba(23,23,23,0.48)_100%)]" />
                    <div className="absolute left-4 top-4 rounded-full bg-surface-1/90 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.24em] text-text-900 backdrop-blur">
                      Featured editorial
                    </div>
                    <div className="absolute bottom-4 left-4 right-4">
                      <div className="max-w-md rounded-[1.4rem] border border-white/15 bg-black/35 p-4 text-surface-0 backdrop-blur-md">
                        <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-surface-0/75">
                          {featuredArticle.category}
                        </p>
                        <h2 className="mt-2 font-serif text-2xl font-bold leading-tight">
                          {featuredArticle.title}
                        </h2>
                        <p className="mt-2 text-sm leading-relaxed text-surface-0/78">
                          {featuredArticle.excerpt}
                        </p>
                        <div className="mt-4 flex items-center justify-between text-[11px] uppercase tracking-[0.2em] text-surface-0/72">
                          <span>{featuredArticle.readTime}</span>
                          <span>{featuredArticle.publishedAt}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-3">
                    <div className="rounded-[1.6rem] border border-border/80 bg-surface-0 p-4">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.26em] text-text-400">
                        Editorial standard
                      </p>
                      <div className="mt-3 font-serif text-4xl font-bold tracking-tight text-text-900">
                        8K
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-text-600">
                        Calm, premium, and precise presentation built for visual discovery.
                      </p>
                    </div>

                    <MiniMetric value="10" label="Worlds" />
                    <MiniMetric value="100%" label="Clear disclosure" />
                    <MiniMetric value="0" label="SaaS clutter" />

                    <div className="overflow-hidden rounded-[1.6rem] border border-border/80 bg-[linear-gradient(135deg,#f7f5f0,#ffffff_60%,#ede8df)] p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-text-400">
                            Brand direction
                          </p>
                          <h3 className="mt-1 font-serif text-xl font-bold text-text-900">
                            AtoZ Editorial Luxe
                          </h3>
                        </div>
                        <Bookmark className="size-5 text-primary-500" />
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {BRAND_NOTES.map((note) => (
                          <span
                            key={note}
                            className="rounded-full border border-border/70 bg-surface-1 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-text-600"
                          >
                            {note}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Container>
      </section>

      <section className="border-y border-border/70 bg-surface-1/55 py-8">
        <Container>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-border/70 bg-surface-0 px-5 py-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-text-400">
                Visual ratio
              </p>
              <p className="mt-2 font-serif text-2xl font-bold text-text-900">70 / 20 / 10</p>
              <p className="mt-1 text-sm text-text-600">Editorial, commerce, and technology in balance.</p>
            </div>
            <div className="rounded-2xl border border-border/70 bg-surface-0 px-5 py-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-text-400">
                Typographic tone
              </p>
              <p className="mt-2 font-serif text-2xl font-bold text-text-900">Lora + Inter</p>
              <p className="mt-1 text-sm text-text-600">Elegant headlines with functional UI typography.</p>
            </div>
            <div className="rounded-2xl border border-border/70 bg-surface-0 px-5 py-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-text-400">
                Surface system
              </p>
              <p className="mt-2 font-serif text-2xl font-bold text-text-900">Ivory + White</p>
              <p className="mt-1 text-sm text-text-600">Warm, calm backgrounds with bronze accents only.</p>
            </div>
            <div className="rounded-2xl border border-border/70 bg-surface-0 px-5 py-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-text-400">
                Visual hierarchy
              </p>
              <p className="mt-2 font-serif text-2xl font-bold text-text-900">Image first</p>
              <p className="mt-1 text-sm text-text-600">Headlines, context, and action follow the imagery.</p>
            </div>
          </div>
        </Container>
      </section>

      <section id="worlds" className="scroll-mt-24 py-16 sm:py-20 lg:py-24">
        <Container>
          <div className="flex flex-col gap-6 border-b border-border/70 pb-8 lg:flex-row lg:items-end lg:justify-between">
            <SectionHeading
              eyebrow="10 Worlds"
              title="Explore the editorial universe"
              description="Each world keeps its own image language and recommendation flow, while the brand stays visually unified."
            />
            <Link
              href="/categories"
              className="inline-flex items-center gap-2 self-start rounded-xl border border-border/80 bg-surface-1 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-text-600 transition-colors hover:bg-surface-0 hover:text-text-900"
            >
              View all worlds
              <ArrowUpRight className="size-4" />
            </Link>
          </div>

          <div className="mt-10 grid auto-rows-[230px] gap-4 md:grid-cols-2 xl:grid-cols-5 xl:auto-rows-[200px]">
            {NICHES.map((niche, index) => {
              const featured = index === 0;
              const wide = index === 3 || index === 6;
              const tall = index === 1 || index === 8;

              return (
                <Link
                  key={niche.slug}
                  href={`/categories/${niche.slug}`}
                  className={[
                    "group relative overflow-hidden rounded-[1.75rem] border border-border/80 bg-surface-1 shadow-[0_24px_60px_-48px_rgba(0,0,0,0.45)] transition duration-300 ease-out hover:-translate-y-1 hover:border-primary-500/40",
                    featured ? "md:col-span-2 md:row-span-2 xl:col-span-2 xl:row-span-2" : "",
                    wide ? "xl:col-span-2" : "",
                    tall ? "md:row-span-2" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <Image
                    src={niche.image}
                    alt={niche.name}
                    fill
                    sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 20vw"
                    className="object-cover transition duration-500 ease-out group-hover:scale-[1.04]"
                  />
                  <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(23,23,23,0.08)_0%,rgba(23,23,23,0.18)_30%,rgba(23,23,23,0.82)_100%)] transition-opacity duration-300 group-hover:opacity-95" />

                  <div className="absolute left-4 top-4 rounded-full border border-white/20 bg-black/20 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-white/85 backdrop-blur-md">
                    0{index + 1} / 10
                  </div>

                  <div className="absolute bottom-0 left-0 right-0 p-4 text-surface-0">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-surface-0/70">
                      {niche.shortName}
                    </p>
                    <h3 className="mt-2 max-w-[18ch] font-serif text-2xl font-bold leading-tight transition-transform duration-300 group-hover:translate-y-[-2px]">
                      {niche.name}
                    </h3>
                    <p className="mt-2 max-w-sm text-sm leading-relaxed text-surface-0/78">
                      {niche.description}
                    </p>
                    <div className="mt-4 inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-surface-0/80">
                      <span>Explore world</span>
                      <ArrowRight className="size-3.5 transition-transform duration-300 group-hover:translate-x-1" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </Container>
      </section>

      <section className="border-y border-border/70 bg-surface-1/55 py-16 sm:py-20 lg:py-24">
        <Container>
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <SectionHeading
              eyebrow="Curated Discoveries"
              title="Editorial stories and products side by side"
              description="The page should feel like a magazine spread first and a commerce layer second."
            />
            <Link
              href="/products"
              className="inline-flex items-center gap-2 self-start rounded-xl border border-border/80 bg-surface-0 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-text-600 transition-colors hover:text-text-900"
            >
              Browse products
              <ArrowUpRight className="size-4" />
            </Link>
          </div>

          <div className="mt-10 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <article className="relative aspect-[16/9] overflow-hidden rounded-[2rem] border border-border/80 bg-surface-0 shadow-[0_28px_70px_-50px_rgba(0,0,0,0.5)]">
              <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr]">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <Image
                  src={featuredArticle.image ?? NICHES[0].image}
                  alt={featuredArticle.title}
                  fill
                  sizes="(max-width: 1024px) 100vw, 55vw"
                  className="object-cover"
                />
                <div className="flex flex-col justify-between p-6 sm:p-8">
                  <div>
                    <Badge variant="accent">Featured editorial</Badge>
                    <h3 className="mt-4 font-serif text-3xl font-bold leading-tight text-text-900">
                      {featuredArticle.title}
                    </h3>
                    <p className="mt-4 text-base leading-relaxed text-text-600">
                      {featuredArticle.excerpt}
                    </p>
                  </div>
                  <div className="mt-6 border-t border-border/70 pt-5">
                    <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.18em] text-text-400">
                      <span>{featuredArticle.category}</span>
                      <span>{featuredArticle.readTime}</span>
                    </div>
                    <div className="mt-5 flex flex-wrap gap-2">
                      {featuredArticle.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full border border-border/70 bg-surface-1 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-text-600"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    <Link
                      href={`/articles/${featuredArticle.slug}`}
                      className="mt-6 inline-flex items-center gap-2 rounded-xl bg-text-900 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-surface-0 transition-colors hover:bg-text-600"
                    >
                      Read the story
                      <ArrowUpRight className="size-4" />
                    </Link>
                  </div>
                </div>
              </div>
            </article>

            <div className="space-y-4">
              <div className="rounded-[2rem] border border-border/80 bg-surface-0 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.26em] text-text-400">
                      Product rail
                    </p>
                    <h3 className="mt-2 font-serif text-2xl font-bold text-text-900">
                      Curated finds worth knowing
                    </h3>
                  </div>
                  <Star className="size-5 fill-primary-500 text-primary-500" />
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  {featuredProducts.map((product) => (
                    <article
                      key={product.slug}
                      className="group overflow-hidden rounded-[1.5rem] border border-border/80 bg-surface-1 transition duration-300 hover:-translate-y-0.5 hover:border-primary-500/40"
                    >
                      <div className="relative aspect-square overflow-hidden bg-surface-2">
                        {product.image ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <Image
                            src={product.image}
                            alt={product.name}
                            fill
                            sizes="(max-width: 640px) 100vw, 25vw"
                            className="object-cover transition duration-500 ease-out group-hover:scale-[1.04]"
                          />
                        ) : null}
                        <div className="absolute right-3 top-3 rounded-full bg-black/55 px-2.5 py-1 text-[11px] font-semibold text-surface-0 backdrop-blur-md">
                          {product.rating ?? 4.8}
                        </div>
                      </div>
                      <div className="p-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold text-text-900">{product.price}</span>
                          <span className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-400">
                            Tested
                          </span>
                        </div>
                        <h4 className="mt-2 font-serif text-lg font-bold text-text-900">
                          {product.name}
                        </h4>
                        <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-text-600">
                          {product.summary}
                        </p>
                      </div>
                    </article>
                  ))}
                </div>
              </div>

              <div className="rounded-[2rem] border border-border/80 bg-[linear-gradient(135deg,#171717,#23211f_48%,#171717)] p-5 text-surface-0">
                <p className="text-[10px] font-semibold uppercase tracking-[0.26em] text-surface-0/65">
                  Editorial note
                </p>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  {featuredStories.slice(1, 3).map((story) => (
                    <Link
                      key={story.slug}
                      href={`/articles/${story.slug}`}
                      className="group rounded-[1.5rem] border border-white/10 bg-white/5 p-4 transition-colors hover:bg-white/8"
                    >
                      <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-surface-0/65">
                        {story.category}
                      </p>
                      <h4 className="mt-2 font-serif text-lg font-bold leading-tight text-surface-0">
                        {story.title}
                      </h4>
                      <p className="mt-2 text-sm leading-relaxed text-surface-0/72">
                        {story.excerpt}
                      </p>
                      <div className="mt-4 inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-surface-0/85">
                        Read story
                        <ArrowUpRight className="size-4 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Container>
      </section>

      <section className="py-16 sm:py-20 lg:py-24">
        <Container>
          <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
            <div className="rounded-[2rem] border border-border/80 bg-text-900 p-6 text-surface-0 shadow-[0_28px_70px_-50px_rgba(0,0,0,0.7)]">
              <p className="text-[10px] font-semibold uppercase tracking-[0.26em] text-surface-0/60">
                Pinterest inspiration
              </p>
              <h3 className="mt-3 font-serif text-3xl font-bold leading-tight">
                Built to flow from pin to page to product without visual friction.
              </h3>
              <p className="mt-4 text-sm leading-relaxed text-surface-0/76">
                The same editorial world should continue from Pinterest into the landing page and then into the article or product detail.
              </p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {pinWorlds.slice(0, 4).map((niche, index) => (
                  <div
                    key={niche.slug}
                    className="rounded-[1.4rem] border border-white/10 bg-white/10 p-4"
                  >
                    <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-surface-0/60">
                      0{index + 1}
                    </p>
                    <h4 className="mt-2 font-serif text-lg font-bold">{niche.shortName}</h4>
                    <p className="mt-1 text-sm text-surface-0/72">{niche.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {pinWorlds.map((niche, index) => (
                <Link
                  key={niche.slug}
                  href={`/landing/${niche.slug}`}
                  className={[
                    "group relative overflow-hidden rounded-[1.7rem] border border-border/80 bg-surface-1 shadow-[0_24px_60px_-48px_rgba(0,0,0,0.45)] transition duration-300 hover:-translate-y-1 hover:border-primary-500/40",
                    index === 0 ? "sm:col-span-2" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <div className="aspect-[2/3] sm:aspect-[3/4]">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <Image
                      src={niche.image}
                      alt={niche.name}
                      fill
                      sizes="(max-width: 640px) 100vw, 50vw"
                      className="object-cover transition duration-500 ease-out group-hover:scale-[1.04]"
                    />
                  </div>
                  <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(17,17,17,0.1)_0%,rgba(17,17,17,0.78)_100%)]" />
                  <div className="absolute inset-x-0 bottom-0 p-4 text-surface-0">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-surface-0/70">
                      Pinterest-ready pin
                    </p>
                    <h4 className="mt-2 max-w-[14ch] font-serif text-2xl font-bold leading-tight">
                      {niche.shortName}
                    </h4>
                    <p className="mt-2 text-sm leading-relaxed text-surface-0/76">
                      Editorial cover copy and brand-safe visual direction.
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </Container>
      </section>

      <section className="border-t border-border/70 bg-surface-1/55 py-16 sm:py-20 lg:py-24">
        <Container>
          <div className="grid gap-8 lg:grid-cols-[1fr_1fr]">
            <div>
              <SectionHeading
                eyebrow="Brand story"
                title="A luxury magazine feel, not a SaaS dashboard"
                description="The brand language is calm and trustworthy: image first, editorial hierarchy, restrained bronze accents, and clear purchase intent only where it matters."
              />
              <div className="mt-8 rounded-[2rem] border border-border/80 bg-surface-0 p-6">
                <div className="grid gap-4 sm:grid-cols-3">
                  <MiniMetric value="01" label="Editorial framing" />
                  <MiniMetric value="02" label="Visual continuity" />
                  <MiniMetric value="03" label="Trust signals" />
                </div>
                <p className="mt-5 text-sm leading-relaxed text-text-600">
                  Every page should feel like it belongs to the same publishing system: premium photography, quiet spacing, measured copy, and product recommendations that read like editorial curation.
                </p>
              </div>
            </div>

            <div className="rounded-[2rem] border border-border/80 bg-text-900 p-6 text-surface-0">
              <p className="text-[10px] font-semibold uppercase tracking-[0.26em] text-surface-0/60">
                Visual rules
              </p>
              <div className="mt-6 space-y-4">
                {[
                  "Warm ivory and white surfaces with charcoal sections for contrast.",
                  "Image-dominant cards with 16px radius and almost invisible shadows.",
                  "Serif headings for editorial moments and Inter for functional UI.",
                  "Clear, calm CTAs such as View Product, Read Story, and Explore World.",
                ].map((rule, index) => (
                  <div key={rule} className="flex items-start gap-4 rounded-[1.4rem] border border-white/10 bg-white/5 p-4">
                    <span className="font-serif text-xl font-bold text-primary-500">
                      0{index + 1}
                    </span>
                    <p className="text-sm leading-relaxed text-surface-0/80">{rule}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Container>
      </section>

      <section className="border-t border-border/70 bg-surface-0 py-16 sm:py-20 lg:py-24">
        <Container>
          <div className="rounded-[2.25rem] border border-border/80 bg-[linear-gradient(135deg,#171717,#23211f_56%,#171717)] p-6 text-surface-0 sm:p-8 lg:p-10">
            <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-surface-0/60">
                  Newsletter
                </p>
                <h3 className="mt-3 font-serif text-3xl font-bold leading-tight sm:text-4xl">
                  Fewer, better things in your inbox.
                </h3>
                <p className="mt-4 max-w-2xl text-sm leading-relaxed text-surface-0/74">
                  A calm weekly digest of editorial picks, product finds, and niche-specific inspiration, with clear disclosure and zero noise.
                </p>
              </div>

              {subscribed ? (
                <div className="rounded-[1.4rem] border border-emerald-400/30 bg-emerald-400/10 p-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="size-5 text-emerald-300" />
                    <p className="text-sm font-medium text-emerald-100">
                      Thank you. You are subscribed to the AtoZ editorial digest.
                    </p>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleNewsletterSubmit} className="grid gap-3 sm:grid-cols-[1fr_auto]">
                  <input
                    type="email"
                    required
                    value={newsletterEmail}
                    onChange={(e) => setNewsletterEmail(e.target.value)}
                    placeholder="Enter your email address"
                    className="h-12 min-w-0 rounded-xl border border-white/10 bg-white/10 px-4 text-sm text-surface-0 placeholder:text-surface-0/45 focus:border-primary-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="inline-flex h-12 items-center justify-center rounded-xl bg-surface-0 px-5 text-[11px] font-semibold uppercase tracking-[0.2em] text-text-900 transition-colors hover:bg-primary-500 hover:text-surface-0"
                  >
                    Subscribe
                  </button>
                </form>
              )}
            </div>
          </div>
        </Container>
      </section>
    </div>
  );
}
