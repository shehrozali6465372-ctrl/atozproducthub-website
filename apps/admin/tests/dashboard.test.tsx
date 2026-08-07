import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DashboardPage from "@/app/(app)/page";
import { expectNoAxeViolations } from "./helpers";

describe("Admin dashboard wireframe", () => {
  it("renders KPIs, charts, and top pages table", async () => {
    const { container } = render(await DashboardPage());

    expect(screen.getByRole("heading", { level: 1, name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("128,430")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Top pages by visits" })).toBeInTheDocument();
    expect(screen.getByText(/AI OS insights/i)).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });
});
