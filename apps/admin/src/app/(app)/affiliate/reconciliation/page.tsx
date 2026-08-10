"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Card,
  DataTable,
  EmptyState,
  SectionHeading,
} from "@atoz/design-system";
import {
  createAdminApiClient,
  type AdminReconciliation,
  type AdminRevenueSummary,
} from "@/lib/api-client";

const RECON_STATUS_VARIANT: Record<string, "neutral" | "success" | "danger" | "info"> = {
  matched: "success",
  mismatch: "danger",
  open: "info",
  closed: "neutral",
};

function formatCurrency(cents: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}

export default function AffiliateReconciliationPage() {
  const [reconciliations, setReconciliations] = useState<AdminReconciliation[]>([]);
  const [summaries, setSummaries] = useState<AdminRevenueSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const client = createAdminApiClient();
        const [recon, daily] = await Promise.all([
          client.affiliate.listReconciliations(),
          client.affiliate.listSummaries(),
        ]);
        if (!cancelled) {
          setReconciliations(recon);
          setSummaries(daily);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Affiliate"
        title="Reconciliation"
        description="Nightly reconciliation runs against network reports, plus the daily revenue read model."
      />
      <Card title="Reconciliation runs">
        {loading ? (
          <EmptyState title="Loading reconciliations…" />
        ) : (
          <DataTable
            caption="Affiliate reconciliations in the active niche"
            columns={[
              { key: "reportedAt", header: "Reported", render: (row) => new Date(row.reportedAt).toLocaleDateString("en-US") },
              { key: "networkId", header: "Network", render: (row) => <code>{row.networkId.slice(0, 8)}…</code> },
              { key: "expectedTotalCents", header: "Expected", render: (row) => formatCurrency(row.expectedTotalCents) },
              { key: "actualTotalCents", header: "Actual", render: (row) => formatCurrency(row.actualTotalCents) },
              { key: "deltaCents", header: "Delta", render: (row) => formatCurrency(row.deltaCents) },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <Badge variant={RECON_STATUS_VARIANT[row.status] ?? "neutral"}>{row.status}</Badge>
                ),
              },
            ]}
            rows={reconciliations}
            emptyLabel="No reconciliation runs yet"
          />
        )}
      </Card>
      <Card title="Daily summaries" description="Read model rolled up from the append-only ledgers.">
        {loading ? (
          <EmptyState title="Loading summaries…" />
        ) : (
          <DataTable
            caption="Daily revenue summaries"
            columns={[
              { key: "summaryDate", header: "Date", render: (row) => row.summaryDate },
              { key: "clicks", header: "Clicks", render: (row) => row.clicks },
              { key: "sales", header: "Sales", render: (row) => row.sales },
              { key: "grossCents", header: "Gross", render: (row) => formatCurrency(row.grossCents, row.currency) },
              { key: "commissionCents", header: "Commission", render: (row) => formatCurrency(row.commissionCents, row.currency) },
            ]}
            rows={summaries}
            emptyLabel="No daily summaries yet"
          />
        )}
      </Card>
    </div>
  );
}
