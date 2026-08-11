import type { Metadata } from "next";
import {
  Badge,
  Button,
  Card,
  ChartCard,
  DataTable,
  KpiCard,
  LineChartView,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient } from "@/lib/api-client";
import { AnalyticsRangeFilter } from "@/components/analytics-range-filter";

export const metadata: Metadata = {
  title: "Revenue",
  robots: { index: false, follow: false },
};

const NETWORK_BREAKDOWN = [
  { id: "net1", network: "Amazon Associates", clicks: 21400, conversions: 842, commission: "$2,918.40", status: "reconciled" },
  { id: "net2", network: "Impact (merchants)", clicks: 8300, conversions: 214, commission: "$1,012.10", status: "reconciled" },
  { id: "net3", network: "ShareASale", clicks: 5100, conversions: 96, commission: "$418.00", status: "pending" },
];

function revenueChart(metricSeries: { date: string; metricKey: string; value: number }[]) {
  const byDate = new Map<string, number>();
  for (const point of metricSeries) {
    if (point.metricKey === "revenue.amount") byDate.set(point.date, point.value);
  }
  return [...byDate.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([date, revenue]) => ({ label: date, revenue }));
}

export default async function RevenuePage({
  searchParams,
}: {
  searchParams: Promise<{ range?: string }>;
}) {
  const { range } = await searchParams;
  const to = new Date();
  const from = new Date(to);
  if (range === "90d") from.setDate(to.getDate() - 90);
  else if (range === "ytd") from.setMonth(0, 1);
  else from.setDate(to.getDate() - 30);
  const iso = (date: Date) => date.toISOString().slice(0, 10);
  const rangeFrom = iso(from);
  const rangeTo = iso(to);

  const api = createAdminApiClient();
  const [overview, metricSeries] = await Promise.all([
    api.analytics.getOverview(rangeFrom, rangeTo),
    api.analytics.getMetricSeries(rangeFrom, rangeTo),
  ]);
  const commissionSeries = revenueChart(metricSeries);
  const conversionRate =
    overview.affiliateClicks > 0 ? (overview.conversions / overview.affiliateClicks) * 100 : 0;

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Monetization"
        title="Revenue"
        description="Attributed affiliate revenue, clicks, and commissions from the analytics read models (M8)."
        action={
          <Button variant="outline" size="sm">
            Run reconciliation
          </Button>
        }
      />
      <AnalyticsRangeFilter active={range ?? "30d"} />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Commission" value={`$${overview.revenueAmount.toLocaleString(undefined, { maximumFractionDigits: 2 })}`} delta="all networks" hint="attributed" />
        <KpiCard label="Affiliate clicks" value={overview.affiliateClicks.toLocaleString()} delta="30d" hint="clicks" />
        <KpiCard label="Conversion rate" value={`${conversionRate.toFixed(2)}%`} delta="30d" hint="conversions / clicks" />
        <KpiCard label="Conversions" value={overview.conversions.toLocaleString()} delta="30d" hint="sales" />
      </div>
      <ChartCard
        title="Commission trend"
        description="Attributed revenue over the selected range"
        srTable={
          <table>
            <caption>Commission by day</caption>
            <tbody>
              {commissionSeries.map((row) => (
                <tr key={row.label}>
                  <th scope="row">{row.label}</th>
                  <td>${row.revenue.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      >
        <LineChartView
          data={commissionSeries}
          series={[{ key: "revenue", name: "Commission ($)", color: "var(--color-success-500)" }]}
          ariaLabel="Commission over the selected range"
        />
      </ChartCard>
      <Card title="Network breakdown" description="Commissions by affiliate network.">
        <DataTable
          caption="Revenue by network"
          columns={[
            { key: "network", header: "Network", render: (row) => <span className="font-medium text-text-900">{row.network}</span> },
            { key: "clicks", header: "Clicks", render: (row) => row.clicks.toLocaleString() },
            { key: "conversions", header: "Conversions", render: (row) => row.conversions.toLocaleString() },
            { key: "commission", header: "Commission", render: (row) => <span className="font-mono font-semibold text-success-500">{row.commission}</span> },
            {
              key: "status",
              header: "Status",
              render: (row) => (
                <Badge variant={row.status === "reconciled" ? "success" : "warning"}>{row.status}</Badge>
              ),
            },
          ]}
          rows={NETWORK_BREAKDOWN}
        />
      </Card>
    </div>
  );
}
