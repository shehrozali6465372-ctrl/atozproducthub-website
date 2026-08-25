import type { Metadata } from "next";
import { ShieldCheck, Compass, Sparkles, Award } from "lucide-react";
import { Breadcrumbs, Container, SectionHeading } from "@atoz/design-system";

export const metadata: Metadata = {
  title: "About",
  description: "Who AtozProductHub is, what we stand for, and how we research.",
};

const VALUES = [
  {
    icon: Compass,
    title: "10 Dedicated Universes",
    description:
      "We build distinct, uncompromised hubs for each niche so enthusiasts get deep, specialized knowledge without irrelevant noise.",
  },
  {
    icon: ShieldCheck,
    title: "Editorial Independence",
    description:
      "Affiliate relationships keep our site independent and free. They never dictate our evaluations, inclusions, or ratings.",
  },
  {
    icon: Sparkles,
    title: "Hand-Curated Standards",
    description:
      "Every guide and product curation is verified against real-world craftsmanship, durability, and practical everyday utility.",
  },
  {
    icon: Award,
    title: "Absolute Transparency",
    description:
      "No hidden sponsorships, no fake review metrics, and zero simulated claims. Disclosures are always front and center.",
  },
];

export default function AboutPage() {
  return (
    <div className="py-8 sm:py-16">
      <Container>
        <Breadcrumbs className="mb-8" items={[{ label: "Home", href: "/" }, { label: "About" }]} />

        <div className="max-w-3xl">
          <SectionHeading
            eyebrow="Editorial Philosophy"
            title="About AtozProductHub"
            description="Products and ideas worth knowing — curated with rigorous standards and refined aesthetics."
          />
        </div>

        {/* Narrative Feature */}
        <div className="mt-12 grid gap-12 lg:grid-cols-12 lg:items-center">
          <div className="lg:col-span-7">
            <div className="space-y-6 text-base sm:text-lg leading-relaxed text-text-700 font-normal">
              <p className="text-xl sm:text-2xl font-serif text-text-900 leading-snug">
                We research products and curate lifestyle guides the way a trusted specialist would:
                plainly, honestly, and with the nuanced details that genuinely matter.
              </p>
              <p>
                The modern internet is flooded with low-quality content and sponsored lists.
                AtozProductHub was created as an antidote: a quiet, high-taste network of 10
                specialized domains spanning architecture, culinary craft, minimalist wellness,
                sustainable style, and productive living.
              </p>
              <p>
                When you explore our recommendations, you can be certain that every piece has been
                vetted for real-world excellence.
              </p>
            </div>
          </div>

          <div className="lg:col-span-5">
            <div className="rounded-3xl border border-border/80 bg-surface-1/60 p-8 shadow-sm">
              <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-primary-500">
                Our Core Promise
              </span>
              <h3 className="mt-3 font-serif text-2xl font-bold text-text-900">
                Craftsmanship over volume.
              </h3>
              <p className="mt-4 text-sm leading-relaxed text-text-600">
                We believe in fewer, better things. Every article we publish and every product we highlight
                must solve a real problem or bring meaningful joy to your daily rituals.
              </p>
              <div className="mt-8 grid grid-cols-2 gap-4 border-t border-border/60 pt-6">
                <div>
                  <div className="font-serif text-3xl font-bold text-text-900">10</div>
                  <div className="text-xs uppercase tracking-wider text-text-500 mt-1">Curated Niches</div>
                </div>
                <div>
                  <div className="font-serif text-3xl font-bold text-text-900">100%</div>
                  <div className="text-xs uppercase tracking-wider text-text-500 mt-1">Independent</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Values Grid */}
        <div className="mt-20 border-t border-border/70 pt-16">
          <div className="text-center max-w-2xl mx-auto">
            <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-primary-500">
              The Pillars
            </span>
            <h2 className="mt-3 font-serif text-3xl sm:text-4xl font-bold text-text-900">
              How We Maintain Trust
            </h2>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {VALUES.map((val) => {
              const Icon = val.icon;
              return (
                <div
                  key={val.title}
                  className="flex flex-col justify-between rounded-2xl border border-border/70 bg-surface-0 p-6 shadow-2xs transition-all hover:border-primary-500/50 hover:shadow-md"
                >
                  <div>
                    <div className="grid size-12 place-items-center rounded-xl bg-surface-1 border border-border/60 text-primary-500">
                      <Icon className="size-5" />
                    </div>
                    <h3 className="mt-5 font-serif text-lg font-bold text-text-900">
                      {val.title}
                    </h3>
                    <p className="mt-2 text-xs leading-relaxed text-text-600">
                      {val.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Container>
    </div>
  );
}

