import type { ReactNode } from "react";
import { Button } from "../primitives/button";
import { Container } from "./container";

export interface HeroProps {
  eyebrow?: string;
  title: ReactNode;
  description?: string;
  primaryCta?: { label: string; href: string };
  secondaryCta?: { label: string; href: string };
}

/** Marketing hero (13 §6 archetype: Hero → sections → CTA). */
export function Hero({ eyebrow, title, description, primaryCta, secondaryCta }: HeroProps) {
  return (
    <section className="border-b border-border bg-surface-1">
      <Container className="py-16 sm:py-24">
        <div className="max-w-3xl">
          {eyebrow ? (
            <p className="text-sm font-semibold uppercase tracking-widest text-primary-500">
              {eyebrow}
            </p>
          ) : null}
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-text-900 sm:text-5xl">
            {title}
          </h1>
          {description ? (
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-text-600">
              {description}
            </p>
          ) : null}
          {primaryCta || secondaryCta ? (
            <div className="mt-8 flex flex-wrap gap-3">
              {primaryCta ? (
                <Button asChild size="lg">
                  <a href={primaryCta.href}>{primaryCta.label}</a>
                </Button>
              ) : null}
              {secondaryCta ? (
                <Button asChild variant="outline" size="lg">
                  <a href={secondaryCta.href}>{secondaryCta.label}</a>
                </Button>
              ) : null}
            </div>
          ) : null}
        </div>
      </Container>
    </section>
  );
}
