import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import AnalyticsPage from "@/app/(app)/analytics/page";
import AutomationPage from "@/app/(app)/automation/page";
import PinterestPage from "@/app/(app)/pinterest/page";
import RevenuePage from "@/app/(app)/revenue/page";
import SettingsPage from "@/app/(app)/settings/page";
import { ThemeProvider } from "@atoz/design-system";
import { expectNoAxeViolations } from "./helpers";

describe("admin wireframe pages", () => {
  it("renders analytics with source donut", async () => {
    const { container } = render(await AnalyticsPage());
    expect(screen.getByRole("heading", { name: "Analytics" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /traffic share by source/i })).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });

  it("renders revenue with network breakdown", async () => {
    const { container } = render(await RevenuePage());
    expect(screen.getByRole("heading", { name: "Revenue" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Revenue by network" })).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });

  it("renders pinterest with account isolation table", async () => {
    const { container } = render(await PinterestPage());
    expect(screen.getByRole("heading", { name: "Pinterest" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Pinterest accounts and health" })).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });

  it("renders automation with rules table", async () => {
    const { container } = render(await AutomationPage());
    expect(screen.getByRole("heading", { name: "Automation" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Automation rules" })).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });

  it("renders settings with site identity form", async () => {
    const { container } = render(
      <ThemeProvider>
        <SettingsPage />
      </ThemeProvider>,
    );
    expect(screen.getByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByLabelText("Site name")).toHaveValue("AtozProductHub");
    await expectNoAxeViolations(container);
  });
});
