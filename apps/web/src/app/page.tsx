import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Container } from "@atoz/design-system";
import { NICHES } from "@/lib/niches";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: SITE.tagline,
  description:
    "Explore carefully curated ideas, products and inspiration across 10 specialized niches.",
};

const TRUST_ITEMS = [
  { label: "Independent Worlds" },
  { label: "Curated Quality" },
  { label: "Useful Guides" },
  { label: "Clear Affiliate Disclosure" },
] as const;

export default function HomePage() {
  return (
    <>
      <section>
        <Container className="pb-16 pt-20 text-center sm:pb-24 sm:pt-28 lg:pb-32 lg:pt-36">
          <span className="mb-8 inline-flex items-center rounded-full border border-border bg-surface-0 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-text-600 shadow-sm">
            {NICHES.length} Independent Content Worlds
          </span>

          <h1 className="mx-auto max-w-5xl font-serif text-5xl font-bold leading-[1.05] tracking-tight text-text-900 sm:text-6xl md:text-7xl lg:text-[5.25rem]">
            Discover Your World.
          </h1>

          <p className="mx-auto mt-7 max-w-2xl text-base leading-relaxed text-text-600 sm:text-lg md:text-xl">
            Explore carefully curated ideas, products and inspiration across{" "}
            {NICHES.length} specialized niches.
          </p>

          <div className="mt-10 flex flex-col justify-center gap-3 sm:flex-row sm:items-center sm:gap-4">
            <Link
              href="#niches"
              className="inline-flex min-h-12 items-center justify-center rounded-lg bg-text-900 px-7 text-xs font-semibold uppercase tracking-[0.12em] text-surface-0 transition-colors duration-200 hover:bg-text-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-text-900"
            >
              Explore Niches
              <ArrowRight aria-hidden="true" className="ml-2 size-4" />
            </Link>
            <Link
              href="/about"
              className="inline-flex min-h-12 items-center justify-center rounded-lg border border-border bg-surface-0 px-7 text-xs font-semibold uppercase tracking-[0.12em] text-text-700 transition-colors duration-200 hover:border-text-300 hover:text-text-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-text-900"
            >
              Learn About Us
            </Link>
          </div>
        </Container>
      </section>

      <section id="niches" className="scroll-mt-20 border-t border-border/40">
        <Container className="py-20 sm:py-28">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-serif text-3xl font-bold tracking-tight text-text-900 sm:text-4xl lg:text-[2.75rem]">
              Explore Our Niches
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-text-600 sm:text-base">
              Choose a world that matches your interests.
            </p>
          </div>

          <ul className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
            {NICHES.map((niche) => (
              <li key={niche.slug}>
                <Link
                  href={`/categories/${niche.slug}`}
                  className="group flex h-full flex-col overflow-hidden rounded-xl border border-border bg-surface-0 transition-all duration-200 hover:-translate-y-1 hover:border-text-200 hover:shadow-lg hover:shadow-text-900/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-text-900"
                >
                  <div className="aspect-[16/10] overflow-hidden bg-surface-1">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={niche.image}
                      alt={niche.name}
                      loading="lazy"
                      decoding="async"
                      className="size-full object-cover transition-transform duration-500 ease-out group-hover:scale-105"
                    />
                  </div>

                  <div className="flex flex-1 flex-col p-5">
                    <h3 className="font-serif text-base font-semibold leading-snug text-text-900">
                      {niche.name}
                    </h3>
                    <p className="mt-2.5 text-xs leading-relaxed text-text-600">
                      {niche.description}
                    </p>
                    <span className="mt-5 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.08em] text-text-700 transition-colors duration-200 group-hover:text-text-900">
                      Enter World
                      <ArrowRight
                        aria-hidden="true"
                        className="size-3.5 transition-transform duration-200 group-hover:translate-x-1"
                      />
                    </span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </Container>
      </section>

      <section className="border-t border-border/40 bg-surface-1/50 py-16 sm:py-20">
        <Container>
          <ul className="flex flex-wrap items-center justify-center gap-x-10 gap-y-6 md:gap-x-20">
            {TRUST_ITEMS.map((item) => (
              <li key={item.label} className="flex flex-col items-center gap-2.5 text-text-400">
                <span
                  aria-hidden="true"
                  className="inline-block size-1.5 rounded-full bg-text-900/20"
                />
                <span className="text-[10px] font-bold uppercase tracking-widest">
                  {item.label}
                </span>
              </li>
            ))}
          </ul>
        </Container>
      </section>
    </>
  );
}
