import type { Metadata } from "next";
import {
  Badge,
  Button,
  Card,
  ChartCard,
  DataTable,
  DonutChartView,
  KpiCard,
  LineChartView,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient } from "@/lib/api-client";
import { FilterBar } from "@/components/filter-bar";

export const metadata: Metadata = {
  title: "Analytics",
  robots: { index: false, follow: false },
};

export default async function AnalyticsPage() {
  const api = createAdminApiClient();
  const [trafficSeries, trafficSources, topPages] = await Promise.all([
    api.dashboard.getTrafficSeries(),
    api.analytics.getTrafficSources(),
    api.dashboard.getTopPages(),
  ]);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Measurement"
        title="Analytics"
        description="Traffic, engagement, and conversion — wireframe mock data until the analytics milestone."
        action={
          <Button variant="outline" size="sm">
            Export
          </Button>
        }
      />
      <FilterBar
        label="Analytics filters"
        options={[
          { value: "30d", label: "Last 30 days" },
          { value: "90d", label: "Last 90 days" },
          { value: "ytd", label: "Year to date" },
        ]}
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Sessions" value="128,430" delta="+12.4%" trend="up" hint="30d" />
        <KpiCard label="Avg. session" value="3m 42s" delta="+0.3%" trend="up" hint="30d" />
        <KpiCard label="Bounce rate" value="41.2%" delta="-2.1%" trend="down" hint="good" />
        <KpiCard label="Pin-attributed" value="58%" delta="+4.0%" trend="up" hint="of sessions" />
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard
          title="Sessions over time"
          className="lg:col-span-2"
          srTable={
            <table>
              <caption>Weekly sessions by source</caption>
              <tbody>
                {trafficSeries.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    <td>{row.pinterest + row.organic + row.direct}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          }
        >
          <LineChartView
            data={trafficSeries.map((row) => ({ ...row, sessions: row.pinterest + row.organic + row.direct }))}
            series={[{ key: "sessions", name: "Sessions", color: "var(--color-primary-500)" }]}
            ariaLabel="Weekly sessions over the last 6 weeks"
          />
        </ChartCard>
        <ChartCard
          title="Traffic sources"
          srTable={
            <table>
              <caption>Traffic share by source</caption>
              <tbody>
                {trafficSources.map((row) => (
                  <tr key={row.name}>
                    <th scope="row">{row.name}</th>
                    <td>{row.value}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          }
        >
          <DonutChartView data={trafficSources} ariaLabel="Traffic share by source" />
        </ChartCard>
      </div>
      <Card title="Top pages" description="Highest-traffic pages this period.">
        <DataTable
          caption="Top pages by visits"
          columns={[
            { key: "path", header: "Page", render: (row) => <span className="font-medium text-primary-500">{row.path}</span> },
            { key: "visits", header: "Visits", render: (row) => row.visits.toLocaleString() },
            { key: "conversion", header: "Conversion", render: (row) => row.conversion },
            { key: "status", header: "Status", render: (row) => <Badge variant={row.status === "published" ? "success" : "warning"}>{row.status}</Badge> },
          ]}
          rows={topPages}
        />
      </Card>
    </div>
  );
}
