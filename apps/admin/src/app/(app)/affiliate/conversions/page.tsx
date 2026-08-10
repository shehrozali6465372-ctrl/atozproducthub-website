"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  DataTable,
  EmptyState,
  SectionHeading,
  Select,
} from "@atoz/design-system";
import {
  createAdminApiClient,
  type AdminRevenueTransaction,
} from "@/lib/api-client";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "paid", label: "Paid" },
];

const STATUS_VARIANT: Record<string, "neutral" | "success" | "danger" | "info"> = {
  pending: "neutral",
  approved: "info",
  rejected: "danger",
  paid: "success",
};

function formatCurrency(cents: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}

export default function AffiliateConversionsPage() {
  const [status, setStatus] = useState("");
  const [rows, setRows] = useState<AdminRevenueTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const items = await createAdminApiClient().affiliate.listRevenue(status || undefined);
        if (!cancelled) setRows(items);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [status]);

  async function transition(id: string, action: "approve" | "reject" | "mark_paid") {
    await createAdminApiClient().affiliate.transitionCommission(id, action);
    const items = await createAdminApiClient().affiliate.listRevenue(status || undefined);
    setRows(items);
  }

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Affiliate"
        title="Conversions & commissions"
        description="Append-only commission ledger. Lifecycle: pending → approved → paid (or pending → rejected)."
      />
      <Card title="Revenue transactions">
        <div className="mb-4 flex justify-end">
          <label className="flex items-center gap-2 text-sm">
            <span className="text-text-600">Status</span>
            <Select
              className="w-44"
              aria-label="Filter conversions by status"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </label>
        </div>
        {loading ? (
          <EmptyState title="Loading conversions…" />
        ) : (
          <DataTable
            caption="Affiliate conversions in the active niche"
            columns={[
              { key: "networkTransactionId", header: "Network TX", render: (row) => <code>{row.networkTransactionId}</code> },
              { key: "commissionCents", header: "Commission", render: (row) => formatCurrency(row.commissionCents, row.currency) },
              { key: "grossCents", header: "Gross", render: (row) => formatCurrency(row.grossCents, row.currency) },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <Badge variant={STATUS_VARIANT[row.status] ?? "neutral"}>{row.status}</Badge>
                ),
              },
              { key: "occurredAt", header: "Occurred", render: (row) => new Date(row.occurredAt).toLocaleDateString("en-US") },
              {
                key: "actions",
                header: "Actions",
                render: (row) => (
                  <div className="flex gap-2">
                    {row.status === "pending" && (
                      <>
                        <Button size="sm" variant="outline" onClick={() => void transition(row.id, "approve")}>
                          Approve
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => void transition(row.id, "reject")}>
                          Reject
                        </Button>
                      </>
                    )}
                    {row.status === "approved" && (
                      <Button size="sm" variant="outline" onClick={() => void transition(row.id, "mark_paid")}>
                        Mark paid
                      </Button>
                    )}
                  </div>
                ),
              },
            ]}
            rows={rows}
            emptyLabel="No conversions yet"
          />
        )}
      </Card>
    </div>
  );
}
