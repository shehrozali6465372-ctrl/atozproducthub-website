import type { FooterGroup, NavItem } from "@atoz/design-system";

export const SITE = {
  name: "AtoZ Product Hub",
  tagline: "Curated products, useful ideas, beautifully organized.",
  url: "https://atozproducthub.com",
  logo: "/brand/atoz-mark.svg",
} as const;

export const NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "Worlds", href: "/categories" },
  { label: "Articles", href: "/articles" },
  { label: "Products", href: "/products" },
  { label: "Collections", href: "/collections" },
  { label: "About", href: "/about" },
];

export const FOOTER_GROUPS: FooterGroup[] = [
  { title: "Explore", links: [
    { label: "All Worlds", href: "/categories" },
    { label: "Editorial Guides", href: "/articles" },
    { label: "Products", href: "/products" },
    { label: "Collections", href: "/collections" },
  ]},
  { title: "Company", links: [
    { label: "About AtoZ", href: "/about" },
    { label: "Contact", href: "/contact" },
    { label: "Privacy", href: "/privacy-policy" },
    { label: "Terms", href: "/terms" },
  ]},
  { title: "Trust", links: [
    { label: "Affiliate Disclosure", href: "/disclaimer" },
    { label: "Editorial Standards", href: "/about" },
  ]},
];
