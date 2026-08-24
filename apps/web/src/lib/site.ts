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
  { label: "Niches", href: "/#niches" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
];

export const FOOTER_GROUPS: FooterGroup[] = [
  {
    title: "Discover",
    links: [
      { label: "Explore Niches", href: "/#niches" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Contact", href: "/contact" },
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
