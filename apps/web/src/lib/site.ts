import type { FooterGroup, NavItem } from "@atoz/design-system";

/** Site-wide brand constants (placeholder values until brand freeze). */
export const SITE = {
  name: "AtozProductHub",
  tagline: "Products worth knowing.",
  // Placeholder canonical origin; finalized by seo-service in a later phase.
  url: "https://atozproducthub.com",
} as const;

export const NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "Articles", href: "/articles/sample-article" },
  { label: "Products", href: "/products/sample-product" },
  { label: "About", href: "/about" },
];

export const FOOTER_GROUPS: FooterGroup[] = [
  {
    title: "Explore",
    links: [
      { label: "Home", href: "/" },
      { label: "Articles", href: "/articles/sample-article" },
      { label: "Products", href: "/products/sample-product" },
      { label: "Collections", href: "/collections/sample-collection" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Contact", href: "/contact" },
      { label: "Sitemap", href: "/sitemap" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy Policy", href: "/privacy-policy" },
      { label: "Terms", href: "/terms" },
      { label: "Disclaimer", href: "/disclaimer" },
    ],
  },
];
