import axe from "axe-core";
import { expect } from "vitest";

/** Minimal matchMedia mock for jsdom (theme + responsive tests). */
export function mockMatchMedia() {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

/** Assert the rendered subtree has no WCAG 2.1 AA violations (axe-core). */
export async function expectNoAxeViolations(container: HTMLElement) {
  const results = await axe.run(container);
  expect(results.violations).toEqual([]);
}
