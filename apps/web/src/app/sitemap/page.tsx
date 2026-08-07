import type { Metadata } from "next";
import { Breadcrumbs, Container, SectionHeading } from "@atoz/design-system";
import { createApiClient } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Sitemap",
  description: "A human-readable index of every section of AtozProductHub.",
  robots: { index: false, follow: true },
};

export default async function SitemapPage() {
  const api = createApiClient();
  const [categories, articles, collections, products] = await Promise.all([
    api.content.listCategories(),
    api.content.listArticles(),
    api.affiliate.listCollections(),
    api.affiliate.listProducts(),
  ]);

  const groups = [
    { title: "Categories", links: categories.map((c) => ({ label: c.name, href: `/categories/${c.slug}` })) },
    { title: "Articles", links: articles.map((a) => ({ label: a.title, href: `/articles/${a.slug}` })) },
    { title: "Collections", links: collections.map((c) => ({ label: c.title, href: `/collections/${c.slug}` })) },
    { title: "Products", links: products.map((p) => ({ label: p.name, href: `/products/${p.slug}` })) },
  ];

  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs className="mb-6" items={[{ label: "Home", href: "/" }, { label: "Sitemap" }]} />
      <SectionHeading title="Sitemap" description="Every section, indexed. XML sitemaps ship with the SEO milestone." />
      <div className="grid gap-8 sm:grid-cols-2">
        {groups.map((group) => (
          <section key={group.title} aria-labelledby={`sitemap-${group.title}`}>
            <h2 id={`sitemap-${group.title}`} className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-400">
              {group.title}
            </h2>
            <ul className="space-y-2">
              {group.links.map((link) => (
                <li key={link.href}>
                  <a href={link.href} className="text-sm text-text-600 hover:text-primary-500 hover:underline">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </Container>
  );
}
