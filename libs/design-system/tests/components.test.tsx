import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "../src/components/primitives/badge";
import { Card } from "../src/components/primitives/card";
import { Breadcrumbs } from "../src/components/navigation/breadcrumbs";
import { DisclosureBadge } from "../src/components/feedback/disclosure-badge";
import { expectNoAxeViolations } from "./helpers";

describe("core components", () => {
  it("Badge renders with status text", () => {
    render(<Badge variant="success">Live</Badge>);
    expect(screen.getByText("Live")).toBeInTheDocument();
  });

  it("Card renders title and content section", () => {
    render(<Card title="Revenue">$1,240</Card>);
    expect(screen.getByRole("heading", { name: "Revenue" })).toBeInTheDocument();
    expect(screen.getByText("$1,240")).toBeInTheDocument();
  });

  it("Breadcrumbs expose navigation semantics", async () => {
    const { container } = render(
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Guides", href: "/guides" },
          { label: "Wireframe" },
        ]}
      />,
    );
    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeInTheDocument();
    expect(screen.getByText("Wireframe")).toHaveAttribute("aria-current", "page");
    await expectNoAxeViolations(container);
  });

  it("DisclosureBadge carries affiliate transparency copy", async () => {
    const { container } = render(<DisclosureBadge />);
    expect(screen.getByText(/affiliate links/i)).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });
});
