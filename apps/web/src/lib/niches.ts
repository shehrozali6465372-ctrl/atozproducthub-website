export interface Niche {
  slug: string;
  name: string;
  shortName: string;
  description: string;
  image: string;
}

export const NICHES: Niche[] = [
  {
    slug: "home-decor",
    name: "Home Decor & Interior Design",
    shortName: "Home Decor",
    description: "Beautiful spaces, smart finds and interior inspiration.",
    image: "/images/niches/home-decor.jpg",
  },
  {
    slug: "food-recipes",
    name: "Food & Recipes",
    shortName: "Food & Recipes",
    description: "Recipes, kitchen ideas and useful finds worth saving.",
    image: "/images/niches/food-recipes.jpg",
  },
  {
    slug: "fashion",
    name: "Fashion & Capsule Wardrobes",
    shortName: "Fashion",
    description: "Timeless style, capsule ideas and thoughtful fashion finds.",
    image: "/images/niches/fashion.jpg",
  },
  {
    slug: "beauty-skincare",
    name: "Beauty & Skincare",
    shortName: "Beauty",
    description: "Skincare, beauty essentials and everyday routines.",
    image: "/images/niches/beauty-skincare.jpg",
  },
  {
    slug: "health-wellness",
    name: "Health, Fitness & Wellness",
    shortName: "Health & Wellness",
    description: "Wellness ideas, fitness inspiration and healthier living.",
    image: "/images/niches/health-wellness.jpg",
  },
  {
    slug: "personal-finance",
    name: "Personal Finance & Printables",
    shortName: "Finance",
    description: "Practical money ideas, planners and useful printables.",
    image: "/images/niches/personal-finance.jpg",
  },
  {
    slug: "diy-crafts",
    name: "DIY & Crafts",
    shortName: "DIY & Crafts",
    description: "Creative projects, tutorials and ideas you can make yourself.",
    image: "/images/niches/diy-crafts.jpg",
  },
  {
    slug: "wedding-planning",
    name: "Wedding Planning",
    shortName: "Wedding",
    description: "Planning inspiration, ideas and details for your special day.",
    image: "/images/niches/wedding-planning.jpg",
  },
  {
    slug: "parenting-kids",
    name: "Parenting, Baby Gear & Kids' Rooms",
    shortName: "Parenting",
    description: "Parenting ideas, baby essentials and inspiring kids' spaces.",
    image: "/images/niches/parenting-kids.jpg",
  },
  {
    slug: "productivity",
    name: "Productivity & Self-Improvement",
    shortName: "Productivity",
    description: "Better routines, productivity ideas and tools for personal growth.",
    image: "/images/niches/productivity.jpg",
  },
];
