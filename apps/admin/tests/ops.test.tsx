import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import AuditPage from "@/app/(app)/audit/page";
import OperationsPage from "@/app/(app)/ops/page";
import OperationsLogsPage from "@/app/(app)/ops/logs/page";
import { expectNoAxeViolations } from "./helpers";

describe("M9 operations pages", () => {
  it("renders the operations dashboard with status, queue, jobs and isolation", async () => {
    const { container } = render(await OperationsPage());

    expect(screen.getByRole("heading", { level: 1, name: "Operations" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Business service status" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Durable queue items" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Recent scheduled job executions" })).toBeInTheDocument();
    expect(screen.getByText("Niche / account isolation")).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });

  it("renders the audit log table", async () => {
    const { container } = render(await AuditPage());

    expect(screen.getByRole("heading", { level: 1, name: "Audit log" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Recent audit records" })).toBeInTheDocument();
    expect(screen.getByText("append-only", { exact: false })).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });

  it("renders operation and webhook logs", async () => {
    const { container } = render(await OperationsLogsPage());

    expect(screen.getByRole("heading", { level: 1, name: "Operations logs" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Recent business operations" })).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Recent webhook deliveries" })).toBeInTheDocument();
    await expectNoAxeViolations(container);
  });
});
