"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Card,
  DataTable,
  EmptyState,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient, type AdminMerchant } from "@/lib/api-client";

const STATUS_VARIANT: Record<string, "success" | "danger"> = {
  active: "success",
  disabled: "danger",
};

export default function AffiliateMerchantsPage() {
  const [merchants, setMerchants] = useState<AdminMerchant[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const items = await createAdminApiClient().affiliate.listMerchants();
        if (!cancelled) setMerchants(items);
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
        title="Merchants"
        description="Merchant/program records inside affiliate networks (global reference data)."
      />
      <Card title="Merchants">
        {loading ? (
          <EmptyState title="Loading merchants…" />
        ) : (
          <DataTable
            caption="Affiliate merchants"
            columns={[
              { key: "name", header: "Name", render: (row) => <span className="font-medium">{row.name}</span> },
              { key: "remoteMerchantId", header: "Remote ID", render: (row) => <code>{row.remoteMerchantId}</code> },
              { key: "networkId", header: "Network", render: (row) => row.networkId },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <Badge variant={STATUS_VARIANT[row.status] ?? "neutral"}>{row.status}</Badge>
                ),
              },
            ]}
            rows={merchants}
            emptyLabel="No merchants registered yet"
          />
        )}
      </Card>
    </div>
  );
}
