import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Breadcrumbs, Container, SectionHeading } from "@atoz/design-system";
import { NICHES } from "@/lib/niches";

export const metadata: Metadata = {
  title: "All Niches & Worlds",
  description: "Explore our 10 dedicated, independent niche hubs — crafted without cross-category distraction.",
};

export default function CategoriesPage() {
  return (
    <div className="py-8 sm:py-16">
      <Container>
        <Breadcrumbs className="mb-8" items={[{ label: "Home", href: "/" }, { label: "Niches" }]} />

        <div className="max-w-3xl">
          <SectionHeading
            eyebrow="10 Dedicated Universes"
            title="Explore All Niches"
            description="Each niche is an independent universe of tested recommendations, editorial guides, and curated gear."
          />
        </div>

        <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          {NICHES.map((niche, idx) => (
            <div
              key={niche.slug}
              className="group relative flex flex-col overflow-hidden rounded-3xl border border-border/80 bg-surface-0 p-4 shadow-sm transition-all duration-300 hover:-translate-y-1.5 hover:border-primary-500/50 hover:shadow-xl"
            >
              {/* High-res Niche Image */}
              <div className="relative aspect-[16/10] w-full overflow-hidden rounded-2xl bg-surface-2">
                <Image
                  src={niche.image}
                  alt={niche.name}
                  fill
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                  className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.08]"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                <div className="absolute top-3 left-3 rounded-full bg-black/40 px-3 py-1 text-xs font-bold uppercase tracking-wider text-white backdrop-blur-md">
                  Universe {idx + 1}
                </div>
                <div className="absolute bottom-3 left-4 right-4">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-amber-300">
                    {niche.shortName}
                  </span>
                  <h3 className="font-serif text-xl font-bold text-white leading-tight">
                    {niche.name}
                  </h3>
                </div>
              </div>

              {/* Details & CTA */}
              <div className="flex flex-1 flex-col justify-between p-3 pt-4">
                <p className="text-sm leading-relaxed text-text-600">
                  {niche.description}
                </p>

                <div className="mt-6 flex items-center justify-between border-t border-border/50 pt-4">
                  <span className="text-xs font-semibold text-text-400">
                    Curated Guides & Gear
                  </span>
                  <Link
                    href={`/categories/${niche.slug}`}
                    className="inline-flex items-center gap-1.5 rounded-full bg-surface-1 px-4 py-2 text-xs font-bold uppercase tracking-wider text-text-900 transition-all hover:bg-text-900 hover:text-surface-0"
                  >
                    <span>Enter</span>
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </div>
  );
}
