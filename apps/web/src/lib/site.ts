import type { FooterGroup, NavItem } from "@atoz/design-system";

/** Site-wide brand constants (placeholder values until brand freeze). */
export const SITE = {
  name: "AtoZ Product Hub",
  tagline: "Discover Your World.",
  // Placeholder canonical origin; finalized by seo-service in a later phase.
  url: "https://atozproducthub.com",
} as const;

export const NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/" },
  { label: "10 Niches", href: "/categories" },
  { label: "Articles", href: "/articles" },
  { label: "Products", href: "/products" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
];

export const FOOTER_GROUPS: FooterGroup[] = [
  {
    title: "Explore Niches",
    links: [
      { label: "Home Decor & Living", href: "/categories/home-decor" },
      { label: "Food & Culinary Recipes", href: "/categories/food-recipes" },
      { label: "Fashion & Capsule Style", href: "/categories/fashion" },
      { label: "Beauty & Skin Health", href: "/categories/beauty-skincare" },
      { label: "Wellness & Mobility", href: "/categories/health-wellness" },
      { label: "All 10 Niches", href: "/categories" },
    ],
  },
  {
    title: "Discovery",
    links: [
      { label: "Editorial Guides", href: "/articles" },
      { label: "Tested Gear & Products", href: "/products" },
      { label: "Editorial Standards", href: "/about" },
      { label: "Search Directory", href: "/search" },
    ],
  },
  {
    title: "Legal & Integrity",
    links: [
      { label: "Affiliate Disclaimer", href: "/disclaimer" },
      { label: "Privacy Policy", href: "/privacy-policy" },
      { label: "Terms of Service", href: "/terms" },
      { label: "Contact Us", href: "/contact" },
    ],
  },
];
