import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "@/app/page";
import { expectNoAxeViolations } from "./helpers";

describe("Home page wireframe", () => {
  it("renders hero, sections, and footer navigation", async () => {
    render(await HomePage());

    expect(screen.getByRole("heading", { level: 1, name: "Products worth knowing." })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Popular articles" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Featured collections" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /kitchen gadgets guide/i }).length).toBeGreaterThan(0);
  });

  it("passes axe accessibility checks", async () => {
    const { container } = render(await HomePage());
    await expectNoAxeViolations(container);
  });
});
