"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Card,
  DataTable,
  EmptyState,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient, type AdminNetwork } from "@/lib/api-client";

const STATUS_VARIANT: Record<string, "success" | "danger"> = {
  active: "success",
  disabled: "danger",
};

export default function AffiliateNetworksPage() {
  const [networks, setNetworks] = useState<AdminNetwork[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const items = await createAdminApiClient().affiliate.listNetworks();
        if (!cancelled) setNetworks(items);
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
        title="Networks"
        description="Global reference table: registered affiliate networks and their webhook secret refs (never the secrets themselves)."
      />
      <Card title="Affiliate networks">
        {loading ? (
          <EmptyState title="Loading networks…" />
        ) : (
          <DataTable
            caption="Registered affiliate networks"
            columns={[
              { key: "code", header: "Code", render: (row) => <code>{row.code}</code> },
              { key: "name", header: "Name", render: (row) => <span className="font-medium">{row.name}</span> },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <Badge variant={STATUS_VARIANT[row.status] ?? "neutral"}>{row.status}</Badge>
                ),
              },
              { key: "feedType", header: "Feed type", render: (row) => row.feedType },
              {
                key: "webhookSecretRef",
                header: "Webhook secret ref",
                render: (row) => (
                  <span className="font-mono text-xs text-text-600">
                    {row.webhookSecretRef || "—"}
                  </span>
                ),
              },
            ]}
            rows={networks}
            emptyLabel="No networks registered yet"
          />
        )}
      </Card>
    </div>
  );
}
