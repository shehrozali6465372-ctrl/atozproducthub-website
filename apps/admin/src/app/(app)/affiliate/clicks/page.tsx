"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Card,
  DataTable,
  EmptyState,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient, type AdminClick } from "@/lib/api-client";

export default function AffiliateClicksPage() {
  const [clicks, setClicks] = useState<AdminClick[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const items = await createAdminApiClient().affiliate.listClicks();
        if (!cancelled) setClicks(items);
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
        title="Clicks"
        description="Append-only click ledger: every resolved /go redirect is recorded here with hashed identifiers — no raw PII."
      />
      <Card title="Click ledger">
        {loading ? (
          <EmptyState title="Loading clicks…" />
        ) : (
          <DataTable
            caption="Affiliate clicks in the active niche"
            columns={[
              { key: "id", header: "Click ID", render: (row) => <code>{row.id.slice(0, 8)}…</code> },
              { key: "linkTokenId", header: "Token", render: (row) => <code>{row.linkTokenId.slice(0, 8)}…</code> },
              { key: "clickedAt", header: "Clicked", render: (row) => new Date(row.clickedAt).toLocaleString("en-US") },
              { key: "referrer", header: "Referrer", render: (row) => row.referrer ?? "—" },
              {
                key: "isBot",
                header: "Type",
                render: (row) => (
                  <Badge variant={row.isBot ? "warning" : "neutral"}>
                    {row.isBot ? "bot" : "human"}
                  </Badge>
                ),
              },
              {
                key: "fraudFlag",
                header: "Fraud",
                render: (row) => (
                  <Badge variant={row.fraudFlag ? "danger" : "neutral"}>
                    {row.fraudFlag ? "flagged" : "clean"}
                  </Badge>
                ),
              },
            ]}
            rows={clicks}
            emptyLabel="No clicks recorded yet"
          />
        )}
      </Card>
    </div>
  );
}
