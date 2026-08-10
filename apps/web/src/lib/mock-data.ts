/**
 * M2 wireframe fixtures — presentation scaffolding only. Real data arrives
 * with Phase 6+ through the API gateway and domain services.
 */

export interface MockArticle {
  slug: string;
  title: string;
  excerpt: string;
  category: string;
  categoryHref: string;
  tags: string[];
  readTime: string;
  publishedAt: string;
  body: string[];
}

export interface MockCategory {
  slug: string;
  name: string;
  description: string;
}

export interface MockTag {
  slug: string;
  name: string;
}

export interface MockCollection {
  slug: string;
  title: string;
  description: string;
  productCount: number;
}

export interface MockProduct {
  slug: string;
  name: string;
  price: string;
  /** Optional until live affiliate data supplies them (M5). */
  rating?: number;
  pros?: string[];
  cons?: string[];
  summary: string;
  /** Server-controlled redirect URL (M5); falls back to "#" for mocks. */
  buyUrl?: string;
  /** Required-disclosure flag from the affiliate business layer (M5). */
  disclosureRequired?: boolean;
}

export interface MockPin {
  slug: string;
  title: string;
  board: string;
  saves: string;
}

export const MOCK_ARTICLES: MockArticle[] = [
  {
    slug: "sample-article",
    title: "The Kitchen Gadgets Guide: What's Actually Worth Buying",
    excerpt:
      "A practical, honest look at the kitchen tools that earn their counter space — and the ones to skip.",
    category: "Kitchen",
    categoryHref: "/categories/kitchen",
    tags: ["kitchen", "buying-guide"],
    readTime: "8 min read",
    publishedAt: "Aug 2, 2026",
    body: [
      "Every year, thousands of new kitchen gadgets promise to change the way you cook. Most of them end up in a drawer. This guide covers the tools our research actually stands behind — and the honest reasons some popular gadgets fail the test.",
      "Start with the essentials: a quality chef's knife, a properly seasoned pan, and a thermometer you trust. These three tools solve more everyday problems than a counter full of specialty devices.",
      "When a gadget does earn its place, it usually has one clear job, a short learning curve, and easy cleanup. Ask yourself whether the tool makes a task you already do faster — not whether it makes a task you never do possible.",
      "Before you buy, check three things: replacement part availability, warranty length, and honest reviews from owners who used it for a year, not a week. That filter removes most regret purchases.",
    ],
  },
  {
    slug: "home-office-essentials",
    title: "Home Office Essentials: Setup That Survives the 9-to-5",
    excerpt:
      "Chairs, lighting, and desk organization — the small upgrades that make long workdays sustainable.",
    category: "Office",
    categoryHref: "/categories/office",
    tags: ["office", "workspace"],
    readTime: "6 min read",
    publishedAt: "Jul 26, 2026",
    body: [
      "A comfortable home office is not about a fancy desk. It is about posture, lighting, and removing friction from your daily routine.",
      "Lighting matters more than most people expect. A warm task light that reduces eye strain costs little and changes how the room feels after dark.",
      "Dedicated storage for cables and papers keeps the visual noise down — and a clear desk measurably reduces decision fatigue.",
    ],
  },
  {
    slug: "travel-pack-light",
    title: "Pack Light, Pack Right: Travel Gear for Carry-On-Only Trips",
    excerpt:
      "The packing cubes, bags, and organizers that turn a one-bag trip from stressful to effortless.",
    category: "Travel",
    categoryHref: "/categories/travel",
    tags: ["travel", "gear"],
    readTime: "7 min read",
    publishedAt: "Jul 12, 2026",
    body: [
      "Carry-on-only travel is about systems, not willpower. The right bag and organizer trio removes the daily chaos of digging through your luggage.",
      "Compression cubes shine for clothing; flat pouches handle chargers and cables. Choose one system and commit to it.",
    ],
  },
];

export const MOCK_CATEGORIES: MockCategory[] = [
  { slug: "kitchen", name: "Kitchen", description: "Cookware, gadgets, and food-prep gear." },
  { slug: "office", name: "Office", description: "Desks, chairs, lighting, and organization." },
  { slug: "travel", name: "Travel", description: "Bags, organizers, and trip essentials." },
];

export const MOCK_TAGS: MockTag[] = [
  { slug: "kitchen", name: "Kitchen" },
  { slug: "buying-guide", name: "Buying Guide" },
  { slug: "office", name: "Office" },
  { slug: "travel", name: "Travel" },
];

export const MOCK_COLLECTIONS: MockCollection[] = [
  {
    slug: "sample-collection",
    title: "Best Kitchen Gadgets of 2026",
    description: "The tools our team actually recommends after months of testing.",
    productCount: 12,
  },
  {
    slug: "home-office-bundles",
    title: "Home Office Starter Kits",
    description: "Complete setups for every budget, from spare-room desks to full studios.",
    productCount: 8,
  },
  {
    slug: "carry-on-guide",
    title: "Carry-On Travel Gear Roundup",
    description: "Bags and organizers that make one-bag travel genuinely easy.",
    productCount: 10,
  },
];

export const MOCK_PRODUCTS: MockProduct[] = [
  {
    slug: "sample-product",
    name: "Everyday Chef's Knife 8\"",
    price: "$89.00",
    rating: 4.7,
    summary:
      "A balanced, low-maintenance chef's knife that holds an edge and handles daily prep comfortably.",
    pros: ["Excellent edge retention", "Comfortable grip for long sessions", "Easy to sharpen at home"],
    cons: ["Premium price point", "Requires hand washing"],
  },
  {
    slug: "cast-iron-skillet",
    name: "Pre-Seasoned Cast Iron Skillet 12\"",
    price: "$45.00",
    rating: 4.8,
    summary: "A do-everything pan that improves with age and sears better than most nonstick.",
    pros: ["Virtually indestructible", "Oven and grill safe", "Improves with use"],
    cons: ["Heavy for some users", "Needs seasoning care"],
  },
  {
    slug: "task-light",
    name: "Adjustable LED Task Lamp",
    price: "$59.00",
    rating: 4.5,
    summary: "Warm, flicker-free task lighting with a small footprint for desks and nightstands.",
    pros: ["Warm dimmable light", "Compact footprint", "USB-C powered"],
    cons: ["Clamp mount only"],
  },
  {
    slug: "packing-cube-set",
    name: "Ultralight Packing Cube Set (3-Pack)",
    price: "$32.00",
    rating: 4.6,
    summary: "Compression cubes that keep one-bag travel organized without adding weight.",
    pros: ["Saves significant space", "Breathable mesh", "Reinforced zippers"],
    cons: ["Limited color options"],
  },
];

export const MOCK_PINS: MockPin[] = [
  {
    slug: "pin-kitchen-gadgets",
    title: "Kitchen gadgets actually worth buying (our 2026 list)",
    board: "Kitchen Buys",
    saves: "12.4k",
  },
  {
    slug: "pin-home-office",
    title: "Home office setup that survives the 9-to-5",
    board: "Office Ideas",
    saves: "8.9k",
  },
  {
    slug: "pin-carry-on",
    title: "Pack light: the one-bag system we swear by",
    board: "Travel Gear",
    saves: "15.1k",
  },
  {
    slug: "pin-cast-iron",
    title: "Why a cast iron skillet earns its spot",
    board: "Kitchen Buys",
    saves: "6.3k",
  },
];

export const MOCK_LANDING_PAGES: Record<string, { title: string; intro: string; articles: MockArticle[]; pins: MockPin[] }> = {
  "kitchen-buys": {
    title: "Kitchen gadgets actually worth buying (our 2026 list)",
    intro:
      "You saved a pin — here is the full guide behind it. Honest testing, clear recommendations, and zero hype.",
    articles: [MOCK_ARTICLES[0]!, MOCK_ARTICLES[1]!],
    pins: MOCK_PINS,
  },
};
