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
import { FilterBar } from "@/components/filter-bar";

export const metadata: Metadata = {
  title: "Revenue",
  robots: { index: false, follow: false },
};

const NETWORK_BREAKDOWN = [
  { id: "net1", network: "Amazon Associates", clicks: 21400, conversions: 842, commission: "$2,918.40", status: "reconciled" },
  { id: "net2", network: "Impact (merchants)", clicks: 8300, conversions: 214, commission: "$1,012.10", status: "reconciled" },
  { id: "net3", network: "ShareASale", clicks: 5100, conversions: 96, commission: "$418.00", status: "pending" },
];

export default async function RevenuePage() {
  const api = createAdminApiClient();
  const revenueSeries = await api.dashboard.getRevenueSeries();

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Monetization"
        title="Revenue"
        description="Affiliate performance and commission tracking — wireframe mock data."
        action={
          <Button variant="outline" size="sm">
            Run reconciliation
          </Button>
        }
      />
      <FilterBar
        label="Revenue filters"
        options={[
          { value: "30d", label: "Last 30 days" },
          { value: "90d", label: "Last 90 days" },
          { value: "ytd", label: "Year to date" },
        ]}
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Commission (30d)" value="$4,128.50" delta="+8.1%" trend="up" hint="all networks" />
        <KpiCard label="Clicks" value="34,800" delta="+6.4%" trend="up" hint="30d" />
        <KpiCard label="Conversion rate" value="3.31%" delta="+0.2%" trend="up" hint="30d" />
        <KpiCard label="Pending payout" value="$418.00" delta="1 network" trend="flat" />
      </div>
      <ChartCard
        title="Commission trend"
        description="Last 6 weeks"
        srTable={
          <table>
            <caption>Weekly commission</caption>
            <tbody>
              {revenueSeries.map((row) => (
                <tr key={row.label}>
                  <th scope="row">{row.label}</th>
                  <td>${row.revenue}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      >
        <LineChartView
          data={revenueSeries}
          series={[{ key: "revenue", name: "Commission ($)", color: "var(--color-success-500)" }]}
          ariaLabel="Weekly commission over the last 6 weeks"
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
