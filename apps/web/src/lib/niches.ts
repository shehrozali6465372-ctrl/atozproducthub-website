export interface Niche {
  slug: string;
  name: string;
  shortName: string;
  description: string;
  gradient: string;
}

export const NICHES: Niche[] = [
  {
    slug: "home-decor",
    name: "Home Decor & Interior Design",
    shortName: "Home Decor",
    description: "Beautiful spaces, smart finds and interior inspiration.",
    gradient: "linear-gradient(135deg, #d4c5b0 0%, #a68b6e 50%, #78624a 100%)",
  },
  {
    slug: "food-recipes",
    name: "Food & Recipes",
    shortName: "Food & Recipes",
    description: "Recipes, kitchen ideas and useful finds worth saving.",
    gradient: "linear-gradient(135deg, #f5deb3 0%, #d4954a 50%, #a0622d 100%)",
  },
  {
    slug: "fashion",
    name: "Fashion & Capsule Wardrobes",
    shortName: "Fashion",
    description: "Timeless style, capsule ideas and thoughtful fashion finds.",
    gradient: "linear-gradient(135deg, #dcd6ce 0%, #9b8e82 50%, #635550 100%)",
  },
  {
    slug: "beauty-skincare",
    name: "Beauty & Skincare",
    shortName: "Beauty",
    description: "Skincare, beauty essentials and everyday routines.",
    gradient: "linear-gradient(135deg, #f2d6dc 0%, #d4939f 50%, #a05e6e 100%)",
  },
  {
    slug: "health-wellness",
    name: "Health, Fitness & Wellness",
    shortName: "Health & Wellness",
    description: "Wellness ideas, fitness inspiration and healthier living.",
    gradient: "linear-gradient(135deg, #c8e6d0 0%, #6bab80 50%, #3d7a52 100%)",
  },
  {
    slug: "personal-finance",
    name: "Personal Finance & Printables",
    shortName: "Finance",
    description: "Practical money ideas, planners and useful printables.",
    gradient: "linear-gradient(135deg, #c8dbe8 0%, #6b95ad 50%, #3d6578 100%)",
  },
  {
    slug: "diy-crafts",
    name: "DIY & Crafts",
    shortName: "DIY & Crafts",
    description: "Creative projects, tutorials and ideas you can make yourself.",
    gradient: "linear-gradient(135deg, #f0dcc0 0%, #c4a06b 50%, #8a6d42 100%)",
  },
  {
    slug: "wedding-planning",
    name: "Wedding Planning",
    shortName: "Wedding",
    description: "Planning inspiration, ideas and details for your special day.",
    gradient: "linear-gradient(135deg, #f5e0e8 0%, #d4a0b8 50%, #a06a88 100%)",
  },
  {
    slug: "parenting-kids",
    name: "Parenting, Baby Gear & Kids' Rooms",
    shortName: "Parenting",
    description: "Parenting ideas, baby essentials and inspiring kids' spaces.",
    gradient: "linear-gradient(135deg, #d0e4ec 0%, #7aacbd 50%, #4a7588 100%)",
  },
  {
    slug: "productivity",
    name: "Productivity & Self-Improvement",
    shortName: "Productivity",
    description: "Better routines, productivity ideas and tools for personal growth.",
    gradient: "linear-gradient(135deg, #ddd8ce 0%, #a09a8e 50%, #6b6558 100%)",
  },
];
