import axe from "axe-core";
import { expect } from "vitest";

/** Assert the rendered subtree has no WCAG 2.1 AA violations (axe-core). */
export async function expectNoAxeViolations(container: HTMLElement) {
  const results = await axe.run(container);
  expect(results.violations).toEqual([]);
}
