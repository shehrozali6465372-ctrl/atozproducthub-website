import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "@/app/page";
import { NICHES } from "@/lib/niches";
import { expectNoAxeViolations } from "./helpers";

describe("AtoZ Product Hub Home Page", () => {
  it("renders the 10-niche gateway and hero CTAs", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { level: 1, name: /discover your world/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: /explore our niches/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /explore niches/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /learn about us/i })).toBeInTheDocument();

    // Verify all 10 niches are present
    expect(NICHES).toHaveLength(10);
    for (const niche of NICHES) {
      expect(screen.getAllByText(niche.name).length).toBeGreaterThan(0);
    }
  });

  it("passes axe accessibility checks", async () => {
    const { container } = render(<HomePage />);
    await expectNoAxeViolations(container);
  });
});

