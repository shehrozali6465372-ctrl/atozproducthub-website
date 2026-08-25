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
  image?: string;
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
  image?: string;
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
    slug: "home-decor-minimalist-lighting",
    title: "Sculptural Lighting & Warm Textures: The 2026 Interior Blueprint",
    excerpt: "How subtle layered light sources, travertine stone, and organic linens transform everyday living spaces.",
    category: "Home Decor & Interior Design",
    categoryHref: "/categories/home-decor",
    tags: ["home-decor", "interior", "lighting"],
    readTime: "7 min read",
    publishedAt: "Aug 18, 2026",
    image: "https://images.unsplash.com/photo-1616489953149-7551745cae7b?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Layering ambient, task, and accent lighting creates warmth without clutter. When selecting fixtures, prioritize dimmable warm LED temperatures between 2700K and 3000K.",
      "Pairing raw materials like linen, unlacquered brass, and travertine stone brings tactile comfort to minimalist spaces.",
    ],
  },
  {
    slug: "sample-article",
    title: "The Kitchen Gadgets Guide: What's Actually Worth Buying",
    excerpt: "A practical, honest look at the kitchen tools that earn their counter space — and the ones to skip.",
    category: "Food & Recipes",
    categoryHref: "/categories/food-recipes",
    tags: ["food-recipes", "kitchen", "buying-guide"],
    readTime: "8 min read",
    publishedAt: "Aug 2, 2026",
    image: "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Every year, thousands of new kitchen gadgets promise to change the way you cook. Most of them end up in a drawer. This guide covers the tools our research actually stands behind — and the honest reasons some popular gadgets fail the test.",
      "Start with the essentials: a quality chef's knife, a properly seasoned pan, and a thermometer you trust. These three tools solve more everyday problems than a counter full of specialty devices.",
    ],
  },
  {
    slug: "capsule-wardrobe-essentials",
    title: "The 30-Piece Capsule Wardrobe: Architectural Tailoring & Natural Fibers",
    excerpt: "Build a timeless, cohesive wardrobe that eliminates decision fatigue while elevating personal style.",
    category: "Fashion & Capsule Wardrobes",
    categoryHref: "/categories/fashion",
    tags: ["fashion", "capsule-wardrobe", "style"],
    readTime: "6 min read",
    publishedAt: "Aug 14, 2026",
    image: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=1200&auto=format&fit=crop",
    body: [
      "A capsule wardrobe is not about restriction; it is about intentional curation. Focusing on silk, wool, and heavy cottons ensures pieces drape gracefully and endure.",
      "Selecting a cohesive palette of ecru, espresso, navy, and charcoal allows effortless mix-and-match combinations.",
    ],
  },
  {
    slug: "skincare-barrier-repair-guide",
    title: "Ceramides, Peptides & Lipids: The Science of Restoring Skin Barrier",
    excerpt: "An evidence-backed guide to soothing irritation and locking in hydration with restorative ingredients.",
    category: "Beauty & Skincare",
    categoryHref: "/categories/beauty-skincare",
    tags: ["beauty-skincare", "skincare", "routine"],
    readTime: "9 min read",
    publishedAt: "Aug 10, 2026",
    image: "https://images.unsplash.com/photo-1556228720-195a672e8a03?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Skin barrier health depends on the delicate balance of ceramides, cholesterol, and fatty acids. Over-exfoliation weakens this protective layer.",
      "Incorporate gentle pH-balanced cleansers and lipid-replenishing moisturizers to protect against environmental stressors.",
    ],
  },
  {
    slug: "longevity-and-mobility-routine",
    title: "Daily Joint Mobility & Recovery: The Longevity Protocol",
    excerpt: "Functional mobility drills and recovery essentials designed for sustainable, lifelong fitness.",
    category: "Health, Fitness & Wellness",
    categoryHref: "/categories/health-wellness",
    tags: ["health-wellness", "fitness", "longevity"],
    readTime: "8 min read",
    publishedAt: "Jul 28, 2026",
    image: "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Daily joint circles, thoracic spine rotations, and hip openers reduce chronic stiffness and enhance athletic performance.",
      "Prioritizing deep restorative sleep and targeted magnesium supplementation compounds physical gains over time.",
    ],
  },
  {
    slug: "automated-budgeting-printables",
    title: "Zero-Based Budgeting: Printables & Frameworks for Cash Flow Clarity",
    excerpt: "Practical templates and automated tracking systems to gain total control over investments and savings.",
    category: "Personal Finance & Printables",
    categoryHref: "/categories/personal-finance",
    tags: ["personal-finance", "budgeting", "planners"],
    readTime: "7 min read",
    publishedAt: "Jul 22, 2026",
    image: "https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Giving every dollar a job before the month starts eliminates guilt around discretionary spending.",
      "Pairing printable debt-payoff trackers with high-yield automated savings accounts accelerates financial independence.",
    ],
  },
  {
    slug: "ceramics-and-leather-crafting",
    title: "Studio Crafting: Hand-Built Ceramics & Vegetable-Tanned Leather",
    excerpt: "Step-by-step guidance on creating heirloom-quality handmade goods in your home workshop.",
    category: "DIY & Crafts",
    categoryHref: "/categories/diy-crafts",
    tags: ["diy-crafts", "woodworking", "handmade"],
    readTime: "10 min read",
    publishedAt: "Jul 15, 2026",
    image: "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Working with natural clay and vegetable-tanned leather connects makers to timeless tactile traditions.",
      "Mastering saddle stitching and burnishing gives DIY leather accessories a boutique-level luxury finish.",
    ],
  },
  {
    slug: "modern-curated-wedding-timeline",
    title: "The Editorial Wedding: Curating Intimate Gatherings & Timeless Details",
    excerpt: "A calm, comprehensive master checklist for photography, tablescapes, and celebration logistics.",
    category: "Wedding Planning",
    categoryHref: "/categories/wedding-planning",
    tags: ["wedding-planning", "stationery", "tablescape"],
    readTime: "11 min read",
    publishedAt: "Jul 08, 2026",
    image: "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Intimate ceremonies allow couples to invest in bespoke typography, local floral artistry, and unforgettable dining.",
      "A generous 12-month timeline relieves stress and ensures seamless coordination between vendors.",
    ],
  },
  {
    slug: "montessori-nursery-sanctuary",
    title: "Montessori Nursery Design: Child-Led Spaces & Non-Toxic Essentials",
    excerpt: "Low floor beds, accessible open shelving, and safe organic materials that foster independence.",
    category: "Parenting, Baby Gear & Kids' Rooms",
    categoryHref: "/categories/parenting-kids",
    tags: ["parenting-kids", "nursery", "baby-gear"],
    readTime: "6 min read",
    publishedAt: "Jun 30, 2026",
    image: "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Low shelving with limited toy rotations encourages deep concentration and natural order in young toddlers.",
      "Choosing solid hardwoods finished with plant-based oils ensures clean indoor air quality for your baby.",
    ],
  },
  {
    slug: "deep-work-and-energy-management",
    title: "Deep Work Architecture: Daily Rhythms & Frictionless Workspaces",
    excerpt: "Time-blocking frameworks, task triage, and physical environment setups that protect focus.",
    category: "Productivity & Self-Improvement",
    categoryHref: "/categories/productivity",
    tags: ["productivity", "focus", "deep-work"],
    readTime: "8 min read",
    publishedAt: "Jun 19, 2026",
    image: "https://images.unsplash.com/photo-1484417894907-623942c8ee29?q=80&w=1200&auto=format&fit=crop",
    body: [
      "Protecting 90-minute uninterrupted deep work blocks produces more meaningful output than 8 hours of fractured multi-tasking.",
      "A clutter-free physical desk and an analog notebook reduce cognitive friction before high-stakes problem solving.",
    ],
  },
];

export const MOCK_CATEGORIES: MockCategory[] = [
  { slug: "home-decor", name: "Home Decor & Interior Design", description: "Beautiful spaces, smart finds and interior inspiration." },
  { slug: "food-recipes", name: "Food & Recipes", description: "Recipes, kitchen ideas and useful finds worth saving." },
  { slug: "fashion", name: "Fashion & Capsule Wardrobes", description: "Timeless style, capsule ideas and thoughtful fashion finds." },
  { slug: "beauty-skincare", name: "Beauty & Skincare", description: "Skincare, beauty essentials and everyday routines." },
  { slug: "health-wellness", name: "Health, Fitness & Wellness", description: "Wellness ideas, fitness inspiration and healthier living." },
  { slug: "personal-finance", name: "Personal Finance & Printables", description: "Practical money ideas, planners and useful printables." },
  { slug: "diy-crafts", name: "DIY & Crafts", description: "Creative projects, tutorials and ideas you can make yourself." },
  { slug: "wedding-planning", name: "Wedding Planning", description: "Planning inspiration, ideas and details for your special day." },
  { slug: "parenting-kids", name: "Parenting, Baby Gear & Kids' Rooms", description: "Parenting ideas, baby essentials and inspiring kids' spaces." },
  { slug: "productivity", name: "Productivity & Self-Improvement", description: "Better routines, productivity ideas and tools for personal growth." },
];

export const MOCK_TAGS: MockTag[] = [
  { slug: "home-decor", name: "Home Decor" },
  { slug: "food-recipes", name: "Food & Recipes" },
  { slug: "fashion", name: "Fashion" },
  { slug: "beauty-skincare", name: "Beauty & Skincare" },
  { slug: "health-wellness", name: "Health & Wellness" },
  { slug: "personal-finance", name: "Personal Finance" },
  { slug: "diy-crafts", name: "DIY & Crafts" },
  { slug: "wedding-planning", name: "Wedding Planning" },
  { slug: "parenting-kids", name: "Parenting & Kids" },
  { slug: "productivity", name: "Productivity" },
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
    image: "https://images.unsplash.com/photo-1593618998160-e34014e67546?q=80&w=1000&auto=format&fit=crop",
    pros: ["Excellent edge retention", "Comfortable grip for long sessions", "Easy to sharpen at home"],
    cons: ["Premium price point", "Requires hand washing"],
  },
  {
    slug: "cast-iron-skillet",
    name: "Pre-Seasoned Cast Iron Skillet 12\"",
    price: "$45.00",
    rating: 4.8,
    summary: "A do-everything pan that improves with age and sears better than most nonstick.",
    image: "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?q=80&w=1000&auto=format&fit=crop",
    pros: ["Virtually indestructible", "Oven and grill safe", "Improves with use"],
    cons: ["Heavy for some users", "Needs seasoning care"],
  },
  {
    slug: "task-light",
    name: "Adjustable LED Task Lamp",
    price: "$59.00",
    rating: 4.5,
    summary: "Warm, flicker-free task lighting with a small footprint for desks and nightstands.",
    image: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?q=80&w=1000&auto=format&fit=crop",
    pros: ["Warm dimmable light", "Compact footprint", "USB-C powered"],
    cons: ["Clamp mount only"],
  },
  {
    slug: "packing-cube-set",
    name: "Ultralight Packing Cube Set (3-Pack)",
    price: "$32.00",
    rating: 4.6,
    summary: "Compression cubes that keep one-bag travel organized without adding weight.",
    image: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=1000&auto=format&fit=crop",
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
