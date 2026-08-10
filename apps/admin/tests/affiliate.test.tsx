import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import AffiliateOverviewPage from "@/app/(app)/affiliate/page";
import AffiliateConversionsPage from "@/app/(app)/affiliate/conversions/page";
import { ThemeProvider } from "@atoz/design-system";
import { MOCK_AFFILIATE_REVENUE } from "@/lib/mock-data";
import { expectNoAxeViolations } from "./helpers";

describe("admin affiliate screens (M5)", () => {
  // The mock ledger mutates in place across transitions; reset so each test
  // starts from the pristine pending fixture regardless of execution order.
  beforeEach(() => {
    MOCK_AFFILIATE_REVENUE[0].status = "pending";
  });
  it("renders the revenue overview with KPIs from the niche-scoped dashboard", async () => {
    const { container } = render(
      <ThemeProvider>
        <AffiliateOverviewPage />
      </ThemeProvider>,
    );
    await waitFor(() => expect(screen.getByRole("heading", { name: "Affiliate" })).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText("Total commissions")).toBeInTheDocument());
    // Mock dashboard: $75.00 lifetime, $25.00 approved, $50.00 pending, $0.00 paid
    expect(screen.getByText("$75.00")).toBeInTheDocument();
    expect(screen.getByText("$25.00")).toBeInTheDocument();
    expect(screen.getByText("$50.00")).toBeInTheDocument();
    expect(screen.getAllByText("$0.00").length).toBeGreaterThan(0);
    
    await expectNoAxeViolations(container);
  });

  it("lists conversions and filters by commission status", async () => {
    const { container } = render(
      <ThemeProvider>
        <AffiliateConversionsPage />
      </ThemeProvider>,
    );
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Conversions & commissions" })).toBeInTheDocument(),
    );
    await waitFor(() => expect(screen.getAllByText("pending").length).toBeGreaterThan(0));
    expect(screen.getAllByText("ntx-1001").length).toBeGreaterThan(0);

    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("Filter conversions by status"), "paid");
    await waitFor(() => expect(screen.getByText("No conversions yet")).toBeInTheDocument());
    await expectNoAxeViolations(container);
  });

  it("approves a pending conversion through the ledger actions", async () => {
    render(
      <ThemeProvider>
        <AffiliateConversionsPage />
      </ThemeProvider>,
    );
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Approve" }).length).toBeGreaterThan(0));
    const user = userEvent.setup();
    await user.click(screen.getAllByRole("button", { name: "Approve" })[0]);
    await waitFor(() => expect(screen.getAllByText("approved").length).toBeGreaterThan(0));
    expect(screen.getAllByRole("button", { name: "Mark paid" }).length).toBeGreaterThan(0);
  });
});
