import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "@/app/page";
import { expectNoAxeViolations } from "./helpers";

describe("Home page wireframe", () => {
  it("renders hero, sections, and footer navigation", async () => {
    render(await HomePage());

    expect(screen.getByRole("heading", { level: 1, name: "Discover Your World." })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Explore Our Niches" })).toBeInTheDocument();

    const expectedNicheLinks = [
      ["Home Decor & Interior Design", "/categories/home-decor"],
      ["Food & Recipes", "/categories/food-recipes"],
      ["Productivity & Self-Improvement", "/categories/productivity"],
    ] as const;

    for (const [name, href] of expectedNicheLinks) {
      expect(screen.getByRole("link", { name: new RegExp(name) })).toHaveAttribute("href", href);
    }
  });

  it("passes axe accessibility checks", async () => {
    const { container } = render(await HomePage());
    await expectNoAxeViolations(container);
  });
});
