import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import ContentPage from "@/app/(app)/content/page";
import NewArticlePage from "@/app/(app)/content/new/page";
import EditArticlePage from "@/app/(app)/content/[id]/page";
import { ThemeProvider } from "@atoz/design-system";
import { expectNoAxeViolations } from "./helpers";

const KITCHEN_GUIDE = "The Kitchen Gadgets Guide: What's Actually Worth Buying";
const HOME_OFFICE = "Home Office Essentials: Setup That Survives the 9-to-5";

describe("admin CMS screens (M4)", () => {
  it("lists articles with a status filter", async () => {
    const { container } = render(
      <ThemeProvider>
        <ContentPage />
      </ThemeProvider>,
    );
    await waitFor(() => expect(screen.getByRole("heading", { name: "Content" })).toBeInTheDocument());
    await waitFor(() =>
      expect(screen.getAllByRole("link", { name: KITCHEN_GUIDE }).length).toBeGreaterThan(0),
    );
    // DataTable renders a desktop table + mobile card list from the same rows.
    expect(screen.getAllByText("published").length).toBeGreaterThan(0);
    expect(screen.getAllByText("draft").length).toBeGreaterThan(0);

    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("Filter articles by status"), "published");
    await waitFor(() =>
      expect(screen.queryAllByRole("link", { name: HOME_OFFICE })).toHaveLength(0),
    );
    expect(screen.getAllByRole("link", { name: KITCHEN_GUIDE }).length).toBeGreaterThan(0);
    await expectNoAxeViolations(container);
  });

  it("shows an empty state when no articles match", async () => {
    render(
      <ThemeProvider>
        <ContentPage />
      </ThemeProvider>,
    );
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("Filter articles by status"), "archived");
    await waitFor(() => expect(screen.getByText("No articles in this status yet")).toBeInTheDocument());
  });

  it("renders the new article form and validates required title", async () => {
    const { container } = render(
      <ThemeProvider>
        <NewArticlePage />
      </ThemeProvider>,
    );
    await waitFor(() => expect(screen.getByLabelText(/^Title/)).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Save draft" }));
    await waitFor(() => expect(screen.getAllByText("Title is required.").length).toBeGreaterThan(0));
    await expectNoAxeViolations(container);
  });

  it("renders the article editor with lifecycle actions and version history", async () => {
    const { container } = render(
      <ThemeProvider>
        <EditArticlePage />
      </ThemeProvider>,
    );
    await waitFor(() => expect(screen.getByRole("heading", { name: KITCHEN_GUIDE })).toBeInTheDocument());
    expect(screen.getAllByText("published").length).toBeGreaterThan(0);
    // published articles offer unpublish + archive, not submit/approve
    expect(screen.getByRole("button", { name: "Unpublish" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Archive" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Submit for review" })).not.toBeInTheDocument();
    expect(screen.getByText(/Version 2 · /)).toBeInTheDocument();
    expect(screen.getByText(/Version 1 · /)).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });

  it("runs a lifecycle transition and reports the new status", async () => {
    render(
      <ThemeProvider>
        <EditArticlePage />
      </ThemeProvider>,
    );
    await waitFor(() => expect(screen.getByRole("button", { name: "Unpublish" })).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Unpublish" }));
    await waitFor(() => expect(screen.getByText('Article moved to "unpublished".')).toBeInTheDocument());
  });

  it("delete button is available on the editor", async () => {
    render(
      <ThemeProvider>
        <EditArticlePage />
      </ThemeProvider>,
    );
    await waitFor(() => expect(screen.getByRole("button", { name: "Delete (soft)" })).toBeInTheDocument());
  });
});
