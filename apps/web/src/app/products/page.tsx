import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, Star } from "lucide-react";
import { Badge, Breadcrumbs, Container, SectionHeading } from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Curated Products & Gear",
  description: "Explore products available through the AtoZ Product Hub catalog, with clear pricing and affiliate disclosure.",
};

export default async function ProductsPage() {
  const products = await createApiClient().affiliate.listProducts();

  return (
    <div className="py-8 sm:py-16">
      <Container>
        <Breadcrumbs className="mb-8" items={[{ label: "Home", href: "/" }, { label: "Products" }]} />
        <div className="max-w-3xl">
          <SectionHeading eyebrow="Product Directory" title="Curated Products & Gear" description="Browse products available through our catalog. Commercial relationships are disclosed wherever they apply." />
        </div>
        {products.length > 0 ? (
          <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {products.map((product) => (
              <div key={product.slug} className="group flex flex-col justify-between overflow-hidden rounded-2xl border border-border/80 bg-surface-0 p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-primary-500/50 hover:shadow-lg">
                <div>
                  <div className="relative aspect-square w-full overflow-hidden rounded-xl bg-surface-2">
                    {product.image ? <Image src={product.image} alt={product.name} fill sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw" className="object-cover transition-transform duration-500 ease-out group-hover:scale-105" /> : <div className="grid size-full place-items-center p-6 text-center text-sm text-text-400">Product image unavailable</div>}
                  </div>
                  <div className="mt-4">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-text-900">{product.price}</span>
                      {product.rating !== undefined ? <span className="inline-flex items-center gap-1 text-xs font-semibold text-text-500"><Star className="size-3 fill-current" /> {product.rating.toFixed(1)}</span> : <Badge variant="neutral">Catalog</Badge>}
                    </div>
                    <h3 className="mt-2 font-serif text-lg font-bold leading-snug text-text-900 transition-colors group-hover:text-primary-500"><Link href={`/products/${product.slug}`}>{product.name}</Link></h3>
                    <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-text-600">{product.summary}</p>
                  </div>
                </div>
                <div className="mt-6 flex items-center justify-between border-t border-border/50 pt-4">
                  <Link href={`/products/${product.slug}`} className="text-xs font-bold uppercase tracking-wider text-text-500 transition-colors hover:text-text-900">View details</Link>
                  <Link href={`/products/${product.slug}`} className="inline-flex items-center gap-1 rounded-full bg-text-900 px-4 py-1.5 text-xs font-bold uppercase tracking-wider text-surface-0 transition-all hover:bg-text-600">Review <ArrowUpRight className="size-3" /></Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-12 rounded-2xl border border-border bg-surface-1 p-10 text-center">
            <h2 className="font-serif text-2xl font-bold text-text-900">No products are published yet</h2>
            <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-text-600">The catalog is currently empty. Products will appear here when they are available through the connected catalog.</p>
          </div>
        )}
      </Container>
    </div>
  );
}
