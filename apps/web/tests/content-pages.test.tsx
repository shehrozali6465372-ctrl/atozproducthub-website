import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ArticlePage from "@/app/articles/[slug]/page";
import NotFound from "@/app/not-found";
import ProductPage from "@/app/products/[slug]/page";
import SearchPage from "@/app/search/page";
import { expectNoAxeViolations } from "./helpers";

describe("content page wireframes", () => {
  it("renders the article page with disclosure", async () => {
    const { container } = render(
      await ArticlePage({ params: Promise.resolve({ slug: "sample-article" }) }),
    );
    expect(screen.getByRole("heading", { level: 1, name: /kitchen gadgets guide/i })).toBeInTheDocument();
    expect(screen.getAllByText(/affiliate links/i).length).toBeGreaterThan(0);
    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });

  it("renders the product page with price and buy action", async () => {
    const { container } = render(
      await ProductPage({ params: Promise.resolve({ slug: "sample-product" }) }),
    );
    expect(screen.getByRole("heading", { level: 1, name: /chef's knife/i })).toBeInTheDocument();
    expect(screen.getByText("$89.00")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Buy now" })).toHaveAttribute("rel", "sponsored nofollow");
    await expectNoAxeViolations(container);
  });

  it("renders search results for a query", async () => {
    render(await SearchPage({ searchParams: Promise.resolve({ q: "kitchen" }) }));
    expect(screen.getByRole("heading", { name: "Search" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /kitchen gadgets guide/i }).length).toBeGreaterThan(0);
  });

  it("renders the 404 recovery page", async () => {
    render(<NotFound />);
    expect(screen.getByRole("heading", { name: "This page wandered off" })).toBeInTheDocument();
  });
});
