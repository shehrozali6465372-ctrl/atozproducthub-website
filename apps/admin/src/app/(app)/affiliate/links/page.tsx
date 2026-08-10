"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Card,
  DataTable,
  EmptyState,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient, type AdminAffiliateLink } from "@/lib/api-client";

const STATUS_VARIANT: Record<string, "success" | "danger" | "warning"> = {
  active: "success",
  disabled: "danger",
  expired: "warning",
};

export default function AffiliateLinksPage() {
  const [links, setLinks] = useState<AdminAffiliateLink[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const items = await createAdminApiClient().affiliate.listLinks();
        if (!cancelled) setLinks(items);
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
        title="Links"
        description="Per-network link registrations. Browser requests only ever reach the server-controlled /go resolver — raw network URLs never leave the backend."
      />
      <Card title="Affiliate links">
        {loading ? (
          <EmptyState title="Loading links…" />
        ) : (
          <DataTable
            caption="Affiliate links in the active niche"
            columns={[
              { key: "productId", header: "Product", render: (row) => <code>{row.productId.slice(0, 8)}…</code> },
              { key: "networkId", header: "Network", render: (row) => <code>{row.networkId.slice(0, 8)}…</code> },
              {
                key: "networkLinkUrl",
                header: "Network URL",
                render: (row) => (
                  <span className="font-mono text-xs text-text-600">{row.networkLinkUrl}</span>
                ),
              },
              { key: "defaultCommissionRate", header: "Rate", render: (row) => row.defaultCommissionRate || "—" },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <Badge variant={STATUS_VARIANT[row.status] ?? "neutral"}>{row.status}</Badge>
                ),
              },
              {
                key: "disclosureRequired",
                header: "Disclosure",
                render: (row) => (
                  <Badge variant={row.disclosureRequired ? "warning" : "neutral"}>
                    {row.disclosureRequired ? "required" : "none"}
                  </Badge>
                ),
              },
            ]}
            rows={links}
            emptyLabel="No affiliate links yet"
          />
        )}
      </Card>
    </div>
  );
}
