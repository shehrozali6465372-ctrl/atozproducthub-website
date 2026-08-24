import {
  Baby,
  ChefHat,
  Gem,
  HeartPulse,
  Home,
  Scissors,
  Shirt,
  Sparkles,
  Target,
  Wallet,
  type LucideIcon,
} from "lucide-react";

export interface Niche {
  slug: string;
  name: string;
  description: string;
  icon: LucideIcon;
  accent: string;
}

export const NICHES: Niche[] = [
  {
    slug: "home-decor",
    name: "Home Decor & Interior Design",
    description: "Beautiful spaces, smart finds and interior inspiration.",
    icon: Home,
    accent: "#8b5e3c",
  },
  {
    slug: "food-recipes",
    name: "Food & Recipes",
    description: "Recipes, kitchen ideas and useful finds worth saving.",
    icon: ChefHat,
    accent: "#d97706",
  },
  {
    slug: "fashion",
    name: "Fashion & Capsule Wardrobes",
    description: "Timeless style, capsule ideas and thoughtful fashion finds.",
    icon: Shirt,
    accent: "#7c3aed",
  },
  {
    slug: "beauty-skincare",
    name: "Beauty & Skincare",
    description: "Skincare, beauty essentials and everyday routines.",
    icon: Sparkles,
    accent: "#db2777",
  },
  {
    slug: "health-wellness",
    name: "Health, Fitness & Wellness",
    description: "Wellness ideas, fitness inspiration and healthier living.",
    icon: HeartPulse,
    accent: "#059669",
  },
  {
    slug: "personal-finance",
    name: "Personal Finance & Printables",
    description: "Practical money ideas, planners and useful printables.",
    icon: Wallet,
    accent: "#0284c7",
  },
  {
    slug: "diy-crafts",
    name: "DIY & Crafts",
    description: "Creative projects, tutorials and ideas you can make yourself.",
    icon: Scissors,
    accent: "#ca8a04",
  },
  {
    slug: "wedding-planning",
    name: "Wedding Planning",
    description: "Planning inspiration, ideas and details for your special day.",
    icon: Gem,
    accent: "#be185d",
  },
  {
    slug: "parenting-kids",
    name: "Parenting, Baby Gear & Kids' Rooms",
    description: "Parenting ideas, baby essentials and inspiring kids' spaces.",
    icon: Baby,
    accent: "#0891b2",
  },
  {
    slug: "productivity",
    name: "Productivity & Self-Improvement",
    description: "Better routines, productivity ideas and tools for personal growth.",
    icon: Target,
    accent: "#4f46e5",
  },
];
