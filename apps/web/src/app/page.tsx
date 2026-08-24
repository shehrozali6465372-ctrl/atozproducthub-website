import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, BookOpen, ShieldCheck, Lightbulb } from "lucide-react";
import { Container } from "@atoz/design-system";
import { NICHES } from "@/lib/niches";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: SITE.tagline,
  description:
    "Explore carefully curated ideas, products and inspiration across 10 specialized niches.",
};

const TRUST_ITEMS = [
  { icon: BookOpen, label: "Carefully Researched" },
  { icon: Lightbulb, label: "Thoughtful Recommendations" },
  { icon: ShieldCheck, label: "Clear Affiliate Disclosure" },
] as const;

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="border-b border-border bg-surface-1">
        <Container className="py-20 sm:py-28 lg:py-32">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-text-900 sm:text-5xl lg:text-6xl">
              Discover Your World.
            </h1>
            <p className="mt-5 text-lg leading-relaxed text-text-600 sm:text-xl">
              Explore carefully curated ideas, products and inspiration across
              {" "}
              {NICHES.length} specialized niches.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <a
                href="#niches"
                className="inline-flex h-12 items-center gap-2 rounded-lg bg-primary-500 px-6 text-base font-semibold text-white transition-colors hover:bg-primary-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
              >
                Explore Niches
                <ArrowRight aria-hidden="true" className="size-4" />
              </a>
              <a
                href="/about"
                className="inline-flex h-12 items-center rounded-lg border border-border bg-surface-0 px-6 text-base font-semibold text-text-900 transition-colors hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
              >
                Learn About Us
              </a>
            </div>
          </div>
        </Container>
      </section>

      {/* 10-Niche Gateway */}
      <section id="niches" className="scroll-mt-16">
        <Container className="py-16 sm:py-24">
          <div className="mx-auto max-w-xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-primary-500">
              Niches
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-text-900 sm:text-3xl">
              Explore Our Niches
            </h2>
            <p className="mt-3 text-text-600">
              Choose a world that matches your interests.
            </p>
          </div>

          <ul className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
            {NICHES.map((niche) => {
              const Icon = niche.icon;
              return (
                <li key={niche.slug}>
                  <Link
                    href={`/categories/${niche.slug}`}
                    className="group flex h-full flex-col rounded-xl border border-border bg-surface-1 p-5 transition-all duration-200 hover:-translate-y-0.5 hover:border-primary-500/30 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                  >
                    <span
                      aria-hidden="true"
                      className="mb-4 grid size-10 place-items-center rounded-lg"
                      style={{ backgroundColor: `${niche.accent}18`, color: niche.accent }}
                    >
                      <Icon className="size-5" />
                    </span>
                    <h3 className="text-sm font-semibold leading-snug text-text-900">
                      {niche.name}
                    </h3>
                    <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-text-600">
                      {niche.description}
                    </p>
                    <span className="mt-auto inline-flex items-center gap-1 pt-4 text-xs font-medium text-primary-500 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
                      Explore
                      <ArrowRight aria-hidden="true" className="size-3" />
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </Container>
      </section>

      {/* Trust strip */}
      <section className="border-t border-border bg-surface-1">
        <Container className="py-10">
          <ul className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 sm:gap-x-12">
            {TRUST_ITEMS.map(({ icon: Icon, label }) => (
              <li key={label} className="flex items-center gap-2 text-sm font-medium text-text-600">
                <Icon aria-hidden="true" className="size-4 text-primary-500" />
                {label}
              </li>
            ))}
          </ul>
        </Container>
      </section>
    </>
  );
}
