export interface Niche {
  slug: string;
  name: string;
  shortName: string;
  description: string;
  image: string;
  gradient: string;
}

export const NICHES: Niche[] = [
  {
    slug: "home-decor",
    name: "Home Decor & Interior Design",
    shortName: "Home Decor",
    description: "Beautiful spaces, smart finds and interior inspiration.",
    image:
      "https://images.unsplash.com/photo-1616489953149-7551745cae7b?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #d4c5b0 0%, #a68b6e 50%, #78624a 100%)",
  },
  {
    slug: "food-recipes",
    name: "Food & Recipes",
    shortName: "Food & Recipes",
    description: "Recipes, kitchen ideas and useful finds worth saving.",
    image:
      "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #f5deb3 0%, #d4954a 50%, #a0622d 100%)",
  },
  {
    slug: "fashion",
    name: "Fashion & Capsule Wardrobes",
    shortName: "Fashion",
    description: "Timeless style, capsule ideas and thoughtful fashion finds.",
    image:
      "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #dcd6ce 0%, #9b8e82 50%, #635550 100%)",
  },
  {
    slug: "beauty-skincare",
    name: "Beauty & Skincare",
    shortName: "Beauty",
    description: "Skincare, beauty essentials and everyday routines.",
    image:
      "https://images.unsplash.com/photo-1556228720-195a672e8a03?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #f2d6dc 0%, #d4939f 50%, #a05e6e 100%)",
  },
  {
    slug: "health-wellness",
    name: "Health, Fitness & Wellness",
    shortName: "Health & Wellness",
    description: "Wellness ideas, fitness inspiration and healthier living.",
    image:
      "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #c8e6d0 0%, #6bab80 50%, #3d7a52 100%)",
  },
  {
    slug: "personal-finance",
    name: "Personal Finance & Printables",
    shortName: "Finance",
    description: "Practical money ideas, planners and useful printables.",
    image:
      "https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #c8dbe8 0%, #6b95ad 50%, #3d6578 100%)",
  },
  {
    slug: "diy-crafts",
    name: "DIY & Crafts",
    shortName: "DIY & Crafts",
    description: "Creative projects, tutorials and ideas you can make yourself.",
    image:
      "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #f0dcc0 0%, #c4a06b 50%, #8a6d42 100%)",
  },
  {
    slug: "wedding-planning",
    name: "Wedding Planning",
    shortName: "Wedding",
    description: "Planning inspiration, ideas and details for your special day.",
    image:
      "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #f5e0e8 0%, #d4a0b8 50%, #a06a88 100%)",
  },
  {
    slug: "parenting-kids",
    name: "Parenting, Baby Gear & Kids' Rooms",
    shortName: "Parenting",
    description: "Parenting ideas, baby essentials and inspiring kids' spaces.",
    image:
      "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #d0e4ec 0%, #7aacbd 50%, #4a7588 100%)",
  },
  {
    slug: "productivity",
    name: "Productivity & Self-Improvement",
    shortName: "Productivity",
    description: "Better routines, productivity ideas and tools for personal growth.",
    image:
      "https://images.unsplash.com/photo-1484417894907-623942c8ee29?q=80&w=800&auto=format&fit=crop",
    gradient: "linear-gradient(135deg, #ddd8ce 0%, #a09a8e 50%, #6b6558 100%)",
  },
];
