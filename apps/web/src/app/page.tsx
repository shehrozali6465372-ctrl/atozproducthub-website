import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { Container } from "@atoz/design-system";
import { NICHES } from "@/lib/niches";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: SITE.tagline,
  description:
    "Explore carefully curated ideas, products and inspiration across 10 specialized niches.",
};

const TRUST_ITEMS = [
  "Carefully Researched",
  "Thoughtful Recommendations",
  "Clear Affiliate Disclosure",
] as const;

export default function HomePage() {
  return (
    <>
      {/* Hero — editorial two-column */}
      <section className="border-b border-border/40">
        <Container className="py-16 sm:py-24 lg:py-32">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            {/* Left — copy */}
            <div className="max-w-lg">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary-500">
                AtoZ Product Hub
              </p>
              <h1 className="mt-4 font-serif text-4xl font-bold leading-[1.1] tracking-tight text-text-900 sm:text-5xl lg:text-6xl">
                Discover Your World.
              </h1>
              <p className="mt-6 max-w-md text-base leading-relaxed text-text-600 sm:text-lg">
                Explore carefully curated ideas, products and inspiration
                across {NICHES.length} specialized niches.
              </p>
              <div className="mt-10 flex flex-wrap items-center gap-3">
                <a
                  href="#niches"
                  className="inline-flex h-12 items-center gap-2 rounded-lg bg-primary-500 px-7 text-sm font-semibold tracking-wide text-white transition-colors hover:bg-primary-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                >
                  Explore Niches
                  <ArrowRight aria-hidden="true" className="size-4" />
                </a>
                <a
                  href="/about"
                  className="inline-flex h-12 items-center rounded-lg border border-border bg-surface-0 px-7 text-sm font-semibold tracking-wide text-text-900 transition-colors hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                >
                  Learn About Us
                </a>
              </div>
            </div>

            {/* Right — visual composition */}
            <div aria-hidden="true" className="hidden grid-cols-3 gap-3 lg:grid">
              {[0, 1, 2, 3, 4, 5].map((i) => {
                const niche = NICHES[i];
                if (!niche) return null;
                const spans = i === 0 ? "col-span-2 row-span-2" : "";
                return (
                  <div
                    key={niche.slug}
                    className={`relative overflow-hidden rounded-xl ${spans}`}
                    style={{ aspectRatio: i === 0 ? "1/1" : "1/1", background: niche.gradient }}
                  >
                    <span className="absolute bottom-3 left-3 max-w-[85%] text-[11px] font-semibold uppercase tracking-wider text-white/90 drop-shadow-sm">
                      {niche.shortName}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </Container>
      </section>

      {/* 10-Niche Gateway */}
      <section id="niches" className="scroll-mt-20">
        <Container className="py-16 sm:py-24">
          <div className="max-w-md">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary-500">
              Niches
            </p>
            <h2 className="mt-3 font-serif text-2xl font-bold tracking-tight text-text-900 sm:text-3xl lg:text-4xl">
              Explore Our Niches
            </h2>
            <p className="mt-3 text-base leading-relaxed text-text-600">
              Choose a world that matches your interests.
            </p>
          </div>

          <ul className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {NICHES.map((niche) => (
              <li key={niche.slug}>
                <Link
                  href={`/categories/${niche.slug}`}
                  className="group block overflow-hidden rounded-xl border border-border/50 bg-surface-0 transition-all duration-200 hover:-translate-y-0.5 hover:border-border hover:shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                >
                  {/* Visual area */}
                  <div
                    className="relative aspect-[4/3] w-full overflow-hidden"
                    style={{ background: niche.gradient }}
                  >
                    <span className="absolute bottom-4 left-4 text-xs font-semibold uppercase tracking-widest text-white/90 drop-shadow-sm">
                      {niche.shortName}
                    </span>
                    <span
                      aria-hidden="true"
                      className="absolute right-4 top-4 opacity-0 transition-opacity duration-200 group-hover:opacity-100"
                    >
                      <ArrowUpRight className="size-4 text-white/80" />
                    </span>
                  </div>
                  {/* Text area */}
                  <div className="p-5">
                    <h3 className="text-sm font-semibold leading-snug tracking-tight text-text-900">
                      {niche.name}
                    </h3>
                    <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-text-600">
                      {niche.description}
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </Container>
      </section>

      {/* Trust strip */}
      <section className="border-t border-border/40 bg-surface-1/60">
        <Container className="py-8">
          <ul className="flex flex-wrap items-center justify-center gap-x-10 gap-y-3">
            {TRUST_ITEMS.map((label) => (
              <li key={label} className="flex items-center gap-2.5 text-sm font-medium tracking-wide text-text-600">
                <span aria-hidden="true" className="inline-block size-1.5 rounded-full bg-primary-500/60" />
                {label}
              </li>
            ))}
          </ul>
        </Container>
      </section>
    </>
  );
}
