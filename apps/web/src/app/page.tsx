"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, ArrowUpRight, Search, ShieldCheck, Sparkles } from "lucide-react";
import { Container } from "@atoz/design-system";
import { NICHES } from "@/lib/niches";

const QUICK_SEARCHES = ["Home Decor", "Fashion", "Beauty", "Wellness", "Finance", "Productivity"];

const PRINCIPLES = [
  { icon: Sparkles, title: "Curated, not crowded", text: "Focused worlds for useful ideas, products, guides, and inspiration." },
  { icon: ShieldCheck, title: "Trust before hype", text: "Clear context and honest commercial presentation, without inflated claims." },
  { icon: ArrowUpRight, title: "Built to discover", text: "A calmer path from inspiration to the next useful thing." },
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  function submitSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = query.trim();
    if (value) router.push(`/search?q=${encodeURIComponent(value)}`);
  }

  return (
    <main className="overflow-hidden">
      <section className="relative border-b border-border/70">
        <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -left-40 -top-40 size-[34rem] rounded-full bg-primary-500/10 blur-3xl" />
          <div className="absolute right-0 top-20 size-[26rem] rounded-full bg-accent-400/10 blur-3xl" />
          <div className="editorial-grid absolute inset-0 opacity-30" />
        </div>
        <Container>
          <div className="grid min-h-[calc(100vh-5rem)] items-center gap-12 py-14 lg:grid-cols-[0.92fr_1.08fr] lg:gap-16 lg:py-20">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary-500/20 bg-primary-500/5 px-4 py-2 text-[10px] font-bold uppercase tracking-[0.24em] text-primary-700 dark:text-primary-300">
                <span className="size-1.5 rounded-full bg-primary-500" />
                Discover with intention
              </div>
              <h1 className="mt-7 max-w-3xl font-serif text-[clamp(3.2rem,7vw,6.5rem)] font-bold leading-[0.9] tracking-[-0.05em] text-text-900">
                Find what fits your world.
              </h1>
              <p className="mt-7 max-w-xl text-base leading-8 text-text-600 sm:text-lg">
                AtoZ Product Hub brings products, ideas, guides, and inspiration into focused worlds—so you can explore less noise and find more of what actually fits.
              </p>
              <form onSubmit={submitSearch} className="mt-8 flex max-w-2xl items-center gap-2 rounded-2xl border border-border bg-surface-1 p-2 shadow-[0_24px_70px_-45px_rgba(0,0,0,0.55)]">
                <div className="grid size-11 shrink-0 place-items-center rounded-xl bg-text-900 text-surface-0"><Search aria-hidden className="size-4" /></div>
                <label htmlFor="home-search" className="sr-only">Search AtoZ Product Hub</label>
                <input id="home-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search products, ideas, guides, or a topic..." className="min-w-0 flex-1 bg-transparent px-2 text-sm font-medium text-text-900 outline-none placeholder:text-text-400" />
                <button type="submit" className="hidden h-11 rounded-xl bg-primary-600 px-5 text-[11px] font-bold uppercase tracking-[0.18em] text-white transition hover:bg-primary-700 sm:block">Search</button>
              </form>
              <div className="mt-5 flex flex-wrap items-center gap-2">
                <span className="mr-1 text-[10px] font-bold uppercase tracking-[0.2em] text-text-400">Explore</span>
                {QUICK_SEARCHES.map((item) => <button key={item} type="button" onClick={() => router.push(`/search?q=${encodeURIComponent(item)}`)} className="rounded-full border border-border/70 bg-surface-1 px-3 py-1.5 text-xs text-text-600 transition hover:border-primary-500/40 hover:text-text-900">{item}</button>)}
              </div>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <a href="#worlds" className="inline-flex h-12 items-center justify-center rounded-xl bg-text-900 px-6 text-[11px] font-bold uppercase tracking-[0.2em] text-surface-0 transition hover:bg-text-700">Explore the worlds <ArrowRight className="ml-2 size-4" /></a>
                <Link href="/articles" className="inline-flex h-12 items-center justify-center rounded-xl border border-border bg-surface-1 px-6 text-[11px] font-bold uppercase tracking-[0.2em] text-text-900 transition hover:bg-surface-0">Read the journal</Link>
              </div>
            </div>

            <div className="relative mx-auto w-full max-w-2xl lg:ml-auto">
              <div className="absolute -inset-5 rounded-[2.5rem] bg-primary-500/5 blur-2xl" />
              <div className="relative rounded-[2rem] border border-border/80 bg-surface-1 p-3 shadow-[0_35px_100px_-55px_rgba(0,0,0,0.6)]">
                <div className="relative aspect-[4/5] overflow-hidden rounded-[1.55rem] sm:aspect-[5/4]">
                  <Image src={NICHES[0].image} alt="Home decor and interior inspiration" fill priority sizes="(max-width: 1024px) 100vw, 52vw" className="object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent" />
                  <div className="absolute left-5 top-5 rounded-full border border-white/20 bg-black/30 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-white backdrop-blur-md">AtoZ / Home</div>
                  <div className="absolute inset-x-5 bottom-5">
                    <div className="max-w-md rounded-2xl border border-white/15 bg-black/30 p-5 text-white backdrop-blur-xl">
                      <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-white/65">One place. Many interests.</p>
                      <h2 className="mt-2 font-serif text-3xl font-bold leading-tight">Explore by world, not by algorithm.</h2>
                      <p className="mt-3 text-sm leading-6 text-white/75">A considered browsing experience for people who want useful discoveries without the clutter.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Container>
      </section>

      <section id="worlds" className="scroll-mt-24 py-20 sm:py-24">
        <Container>
          <div className="flex flex-col justify-between gap-6 border-b border-border/70 pb-8 md:flex-row md:items-end">
            <div className="max-w-2xl">
              <p className="text-[10px] font-bold uppercase tracking-[0.28em] text-primary-600 dark:text-primary-300">The AtoZ worlds</p>
              <h2 className="mt-3 font-serif text-4xl font-bold tracking-tight text-text-900 sm:text-5xl">Start with what matters to you.</h2>
              <p className="mt-4 text-base leading-7 text-text-600">Ten focused categories make it easier to browse deeply while keeping discovery relevant.</p>
            </div>
            <Link href="/categories" className="inline-flex items-center text-sm font-semibold text-text-900 transition hover:text-primary-600">View all worlds <ArrowRight className="ml-2 size-4" /></Link>
          </div>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {NICHES.map((niche, index) => (
              <Link key={niche.slug} href={`/categories/${niche.slug}`} className="group">
                <article className="overflow-hidden rounded-2xl border border-border/80 bg-surface-1 transition duration-300 hover:-translate-y-1 hover:border-primary-500/30 hover:shadow-[0_25px_65px_-45px_rgba(0,0,0,0.7)]">
                  <div className="relative aspect-[4/3] overflow-hidden">
                    <Image src={niche.image} alt={niche.name} fill sizes="(max-width: 768px) 100vw, (max-width: 1280px) 33vw, 20vw" className="object-cover transition duration-500 group-hover:scale-105" />
                    <div className="absolute left-3 top-3 rounded-full bg-black/35 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.18em] text-white backdrop-blur">{String(index + 1).padStart(2, "0")}</div>
                  </div>
                  <div className="p-5">
                    <h3 className="font-serif text-xl font-bold text-text-900 group-hover:text-primary-700 dark:group-hover:text-primary-300">{niche.shortName}</h3>
                    <p className="mt-2 text-sm leading-6 text-text-600">{niche.description}</p>
                    <span className="mt-4 inline-flex items-center text-[10px] font-bold uppercase tracking-[0.18em] text-text-500">Enter world <ArrowUpRight className="ml-1.5 size-3.5" /></span>
                  </div>
                </article>
              </Link>
            ))}
          </div>
        </Container>
      </section>

      <section className="border-y border-border/70 bg-surface-1/55 py-20 sm:py-24">
        <Container>
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.28em] text-primary-600 dark:text-primary-300">Our approach</p>
              <h2 className="mt-3 font-serif text-4xl font-bold tracking-tight text-text-900 sm:text-5xl">Useful first. Beautiful by design.</h2>
              <p className="mt-5 max-w-lg text-base leading-7 text-text-600">AtoZ is designed as a destination, not a wall of affiliate links. Content, commerce, and interface should all make the decision easier.</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {PRINCIPLES.map(({ icon: Icon, title, text }) => (
                <div key={title} className="rounded-2xl border border-border/80 bg-surface-0 p-6">
                  <div className="grid size-11 place-items-center rounded-xl bg-primary-500/10 text-primary-600 dark:text-primary-300"><Icon className="size-5" aria-hidden /></div>
                  <h3 className="mt-5 font-serif text-xl font-bold text-text-900">{title}</h3>
                  <p className="mt-3 text-sm leading-6 text-text-600">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </Container>
      </section>

      <section className="py-20 sm:py-24">
        <Container>
          <div className="relative overflow-hidden rounded-[2rem] bg-text-900 px-7 py-12 text-surface-0 sm:px-12 sm:py-16">
            <div aria-hidden className="absolute -right-24 -top-24 size-72 rounded-full bg-primary-500/20 blur-3xl" />
            <div className="relative max-w-3xl">
              <p className="text-[10px] font-bold uppercase tracking-[0.28em] text-primary-300">Your next discovery</p>
              <h2 className="mt-3 font-serif text-4xl font-bold tracking-tight sm:text-5xl">Less noise. Better finds.</h2>
              <p className="mt-5 max-w-2xl text-base leading-7 text-surface-0/70">Choose a world, follow an idea, or search for exactly what you need. AtoZ is built to make useful discovery feel effortless.</p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <a href="#worlds" className="inline-flex h-12 items-center justify-center rounded-xl bg-surface-0 px-6 text-[11px] font-bold uppercase tracking-[0.2em] text-text-900 transition hover:bg-surface-100">Explore worlds <ArrowRight className="ml-2 size-4" /></a>
                <Link href="/about" className="inline-flex h-12 items-center justify-center rounded-xl border border-white/20 px-6 text-[11px] font-bold uppercase tracking-[0.2em] text-white transition hover:bg-white/10">About AtoZ</Link>
              </div>
            </div>
          </div>
        </Container>
      </section>
    </main>
  );
}
