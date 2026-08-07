"use client";

import { Input } from "../forms/input";
import { Button } from "../primitives/button";
import { Container } from "./container";

/**
 * Newsletter capture strip (home wireframe). UI-only in M2; the newsletter
 * feature itself ships in a later milestone — this form is inert by design.
 */
export function NewsletterStrip() {
  return (
    <section aria-labelledby="newsletter-title" className="border-t border-border bg-surface-1">
      <Container className="py-12 sm:py-16">
        <div className="mx-auto max-w-xl text-center">
          <h2 id="newsletter-title" className="text-xl font-bold text-text-900">
            Stay in the loop
          </h2>
          <p className="mt-2 text-sm text-text-600">
            New guides and product roundups, occasionally. (Wireframe — the
            newsletter ships in a later milestone.)
          </p>
          <form
            aria-label="Newsletter signup"
            className="mt-6 flex flex-col gap-2 sm:flex-row"
            onSubmit={(event) => event.preventDefault()}
          >
            <label htmlFor="newsletter-email" className="sr-only">
              Email address
            </label>
            <Input
              id="newsletter-email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              className="flex-1"
            />
            <Button type="submit">Sign up</Button>
          </form>
        </div>
      </Container>
    </section>
  );
}
