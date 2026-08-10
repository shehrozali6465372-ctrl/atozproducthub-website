"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, EmptyState, KpiCard, SectionHeading } from "@atoz/design-system";
import {
  createAdminApiClient,
  type AdminRevenueDashboard,
  type AdminRevenueSummary,
} from "@/lib/api-client";

function formatCurrency(cents: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}

export default function AffiliateOverviewPage() {
  const [dashboard, setDashboard] = useState<AdminRevenueDashboard | null>(null);
  const [summaries, setSummaries] = useState<AdminRevenueSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const client = createAdminApiClient();
        const [kpis, daily] = await Promise.all([
          client.affiliate.revenueDashboard(),
          client.affiliate.listSummaries(),
        ]);
        if (!cancelled) {
          setDashboard(kpis);
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
        eyebrow="Monetization"
        title="Affiliate"
        description="Networks, offers, links, clicks, conversions, commissions, and reconciliation for the active niche."
      />
      {loading ? (
        <EmptyState title="Loading affiliate overview…" />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="Total commissions"
              value={formatCurrency(dashboard?.totalCommissionCents ?? 0)}
              delta="lifetime"
              trend="up"
            />
            <KpiCard
              label="Approved"
              value={formatCurrency(dashboard?.approvedCommissionCents ?? 0)}
              delta="awaiting payout"
              trend="up"
            />
            <KpiCard
              label="Pending"
              value={formatCurrency(dashboard?.pendingCommissionCents ?? 0)}
              delta="under review"
              trend="flat"
            />
            <KpiCard
              label="Paid"
              value={formatCurrency(dashboard?.paidCommissionCents ?? 0)}
              delta="received"
              trend="up"
            />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="This niche" description={`${dashboard?.clickCount ?? 0} clicks · ${dashboard?.transactionCount ?? 0} conversions tracked.`}>
              <ul className="space-y-2 text-sm">
                {[
                  ["Networks", "/affiliate/networks"],
                  ["Merchants", "/affiliate/merchants"],
                  ["Products & offers", "/affiliate/products"],
                  ["Affiliate links", "/affiliate/links"],
                ].map(([label, href]) => (
                  <li key={href}>
                    <Link href={href} className="text-primary-500 hover:underline">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </Card>
            <Card title="Daily revenue" description="Latest rollup row for the active niche.">
              {summaries.length === 0 ? (
                <p className="text-sm text-text-600">No daily summaries yet.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {summaries.slice(0, 5).map((row) => (
                    <li
                      key={row.id}
                      className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
                    >
                      <span className="text-text-600">{row.summaryDate}</span>
                      <span className="font-medium">
                        {row.sales} sales · {formatCurrency(row.commissionCents, row.currency)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
