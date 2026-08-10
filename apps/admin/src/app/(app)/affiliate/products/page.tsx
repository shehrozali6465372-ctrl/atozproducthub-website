"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Card,
  DataTable,
  EmptyState,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient, type AdminProduct } from "@/lib/api-client";

const STATUS_VARIANT: Record<string, "neutral" | "success" | "danger" | "info"> = {
  draft: "neutral",
  active: "success",
  disabled: "danger",
  archived: "info",
};

function formatCurrency(cents: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}

export default function AffiliateProductsPage() {
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const items = await createAdminApiClient().affiliate.listProducts();
        if (!cancelled) setProducts(items);
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
        title="Products & offers"
        description="Niche-scoped product catalog. A product can only go live with an active disclosure-required affiliate link."
      />
      <Card title="Products">
        {loading ? (
          <EmptyState title="Loading products…" />
        ) : (
          <DataTable
            caption="Affiliate products in the active niche"
            columns={[
              { key: "name", header: "Name", render: (row) => <span className="font-medium">{row.name}</span> },
              { key: "sku", header: "SKU", render: (row) => <code>{row.sku}</code> },
              {
                key: "priceCents",
                header: "Price",
                render: (row) => formatCurrency(row.priceCents, row.currency),
              },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <Badge variant={STATUS_VARIANT[row.status] ?? "neutral"}>{row.status}</Badge>
                ),
              },
              { key: "slug", header: "Slug", render: (row) => <span className="text-text-600">/{row.slug}</span> },
            ]}
            rows={products}
            emptyLabel="No products in this niche yet"
          />
        )}
      </Card>
    </div>
  );
}
