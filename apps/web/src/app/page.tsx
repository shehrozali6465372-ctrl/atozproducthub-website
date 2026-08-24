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
] as const;

export default function HomePage() {
  return (
    <>
      {/* Hero — centered editorial */}
      <section>
        <Container className="pt-28 pb-16 text-center sm:pt-36 sm:pb-24 lg:pt-44 lg:pb-32">
          <h1 className="mx-auto max-w-4xl font-serif text-5xl font-bold leading-[1.08] tracking-tight text-text-900 sm:text-6xl md:text-7xl lg:text-8xl">
            Discover Your World.
          </h1>
          <p className="mx-auto mt-8 max-w-xl font-serif italic text-lg leading-relaxed text-text-600 sm:text-xl md:text-2xl">
            Explore carefully curated ideas, products and inspiration across{" "}
            {NICHES.length} specialized niches.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <a
              href="#niches"
              className="inline-flex h-14 items-center rounded-full bg-text-900 px-10 text-xs font-bold uppercase tracking-[0.2em] text-surface-0 transition-colors hover:bg-text-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-text-900 dark:bg-surface-0 dark:text-text-900 dark:hover:bg-surface-1"
            >
              Explore Niches
            </a>
          </div>
        </Container>
      </section>

      {/* 10-Niche Gateway */}
      <section id="niches" className="scroll-mt-20 border-t border-border/40">
        <Container className="py-20 sm:py-28">
          <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-text-400">
                The 10 Worlds
              </p>
              <h2 className="mt-2 font-serif text-3xl font-bold tracking-tight text-text-900 sm:text-4xl lg:text-5xl">
                Explore Our Niches
              </h2>
            </div>
            <p className="text-xs font-bold uppercase tracking-widest text-text-400">
              Choose a world that matches your interests.
            </p>
          </div>

          <ul className="mt-16 grid grid-cols-1 gap-x-8 gap-y-16 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
            {NICHES.map((niche) => (
              <li key={niche.slug}>
                <Link
                  href={`/categories/${niche.slug}`}
                  className="group block cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-text-900"
                >
                  {/* Image — grayscale to color on hover */}
                  <div className="mb-6 aspect-[4/5] overflow-hidden rounded-sm bg-surface-1">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={niche.image}
                      alt={niche.name}
                      loading="lazy"
                      decoding="async"
                      className="size-full object-cover grayscale transition-all duration-700 ease-out group-hover:scale-110 group-hover:grayscale-0"
                    />
                  </div>
                  {/* Text */}
                  <h3 className="font-serif text-lg leading-snug text-text-900 transition-all group-hover:italic">
                    {niche.name}
                  </h3>
                  <p className="mt-2 line-clamp-2 text-[11px] uppercase leading-relaxed tracking-wide text-text-400">
                    {niche.description}
                  </p>
                  <div className="mt-4 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-text-400 transition-colors group-hover:text-text-900">
                    Enter World
                    <ArrowRight aria-hidden="true" className="size-3 transition-transform group-hover:translate-x-2" />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </Container>
      </section>

      {/* Trust strip */}
      <section className="border-t border-border/40 bg-surface-1/50 py-16 sm:py-20">
        <Container>
          <ul className="flex flex-wrap items-center justify-center gap-x-12 gap-y-6 md:gap-x-24">
            {TRUST_ITEMS.map((item) => (
              <li key={item.label} className="flex flex-col items-center gap-2.5 text-text-400">
                <span aria-hidden="true" className="inline-block size-1.5 rounded-full bg-text-900/20 dark:bg-text-900/40" />
                <span className="text-[10px] font-bold uppercase tracking-widest">{item.label}</span>
              </li>
            ))}
          </ul>
        </Container>
      </section>
    </>
  );
}
