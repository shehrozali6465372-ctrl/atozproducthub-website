"use client";

import { useState, type MouseEvent } from "react";
import { Button } from "@atoz/design-system";

interface AffiliateBuyButtonProps {
  /** Absolute URL to the server-controlled /go/{token} resolver. */
  goUrl: string;
  label?: string;
}

/**
 * Affiliate CTA (M5): the /go endpoint returns the stored destination as
 * JSON — never a raw network URL in the DOM. On click the component resolves
 * the signed token and redirects; while resolving it keeps the button
 * disabled so double-clicks cannot record duplicate clicks.
 */
export function AffiliateBuyButton({ goUrl, label = "Buy now" }: AffiliateBuyButtonProps) {
  const [pending, setPending] = useState(false);

  async function onClick(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    try {
      const response = await fetch(goUrl, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error(`go resolution failed: ${response.status}`);
      }
      const data = (await response.json()) as { destination_url: string };
      window.location.assign(data.destination_url);
    } catch {
      setPending(false);
    }
  }

  return (
    <Button asChild size="lg" aria-busy={pending}>
      <a
        href={goUrl}
        rel="sponsored nofollow"
        aria-disabled={pending}
        onClick={onClick}
      >
        {pending ? "Resolving…" : label}
      </a>
    </Button>
  );
}
