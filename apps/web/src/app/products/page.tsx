import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight, Star } from "lucide-react";
import { Badge, Breadcrumbs, Container, SectionHeading } from "@atoz/design-system";
import { MOCK_PRODUCTS } from "@/lib/mock-data";

export const metadata: Metadata = {
  title: "Curated Products & Tested Gear",
  description: "Explore rigorously tested and hand-selected products across our 10 lifestyle niches.",
};

export default function ProductsPage() {
  return (
    <div className="py-8 sm:py-16">
      <Container>
        <Breadcrumbs className="mb-8" items={[{ label: "Home", href: "/" }, { label: "Products" }]} />

        <div className="max-w-3xl">
          <SectionHeading
            eyebrow="Tested Catalog"
            title="Curated Products & Tested Gear"
            description="Every item in our directory has earned its place through durability, performance, and real-world value."
          />
        </div>

        <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {MOCK_PRODUCTS.map((prod) => (
            <div
              key={prod.slug}
              className="group flex flex-col justify-between overflow-hidden rounded-2xl border border-border/80 bg-surface-0 p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-primary-500/50 hover:shadow-lg"
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
                    <span className="inline-flex items-center gap-1 rounded-full bg-black/60 px-2.5 py-1 text-xs font-bold text-amber-300 backdrop-blur-md">
                      <Star className="size-3 fill-amber-300 text-amber-300" />
                      {prod.rating}
                    </span>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-text-900">{prod.price}</span>
                    <Badge variant="neutral">Verified</Badge>
                  </div>
                  <h3 className="mt-2 font-serif text-lg font-bold text-text-900 leading-snug group-hover:text-primary-500 transition-colors">
                    <Link href={`/products/${prod.slug}`}>
                      {prod.name}
                    </Link>
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-text-600 line-clamp-2">
                    {prod.summary}
                  </p>
                </div>
              </div>

              <div className="mt-6 border-t border-border/50 pt-4 flex items-center justify-between">
                <Link
                  href={`/products/${prod.slug}`}
                  className="text-xs font-bold uppercase tracking-wider text-text-500 hover:text-text-900 transition-colors"
                >
                  View Details
                </Link>
                <Link
                  href={`/products/${prod.slug}`}
                  className="inline-flex items-center gap-1 rounded-full bg-text-900 px-4 py-1.5 text-xs font-bold uppercase tracking-wider text-surface-0 transition-all hover:bg-text-600"
                >
                  <span>Review</span>
                  <ArrowUpRight className="size-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </div>
  );
}
