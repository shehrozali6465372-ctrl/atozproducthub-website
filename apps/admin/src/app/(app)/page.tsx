import type { Metadata } from "next";
import {
  Badge,
  Card,
  ChartCard,
  DataTable,
  DisclosureBadge,
  KpiCard,
  LineChartView,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Dashboard",
  robots: { index: false, follow: false },
};

export default async function DashboardPage() {
  const api = createAdminApiClient();
  const [kpis, revenueSeries, trafficSeries, topPages] = await Promise.all([
    api.dashboard.getKpis(),
    api.dashboard.getRevenueSeries(),
    api.dashboard.getTrafficSeries(),
    api.dashboard.getTopPages(),
  ]);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Overview"
        title="Dashboard"
        description="Daily operations at a glance — all figures are wireframe mock data."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <KpiCard key={kpi.label} {...kpi} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Revenue trend"
          description="Last 6 weeks, all affiliate networks"
          srTable={
            <table>
              <caption>Weekly revenue</caption>
              <tbody>
                {revenueSeries.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    <td>{row.revenue}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          }
        >
          <LineChartView
            data={revenueSeries}
            series={[{ key: "revenue", name: "Revenue ($)", color: "var(--color-primary-500)" }]}
            ariaLabel="Weekly revenue over the last 6 weeks"
          />
        </ChartCard>
        <ChartCard
          title="Traffic by source"
          description="Pinterest vs organic vs direct"
          srTable={
            <table>
              <caption>Weekly traffic by source</caption>
              <tbody>
                {trafficSeries.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    <td>Pinterest {row.pinterest}</td>
                    <td>Organic {row.organic}</td>
                    <td>Direct {row.direct}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          }
        >
          <LineChartView
            data={trafficSeries}
            series={[
              { key: "pinterest", name: "Pinterest", color: "var(--color-danger-500)" },
              { key: "organic", name: "Organic", color: "var(--color-primary-500)" },
              { key: "direct", name: "Direct", color: "var(--color-success-500)" },
            ]}
            ariaLabel="Weekly traffic by source over the last 6 weeks"
          />
        </ChartCard>
      </div>

      <Card title="Top pages" description="Highest-traffic business pages this period.">
        <DataTable
          caption="Top pages by visits"
          columns={[
            { key: "path", header: "Page", render: (row) => <span className="font-medium text-primary-500">{row.path}</span> },
            { key: "visits", header: "Visits", render: (row) => row.visits.toLocaleString() },
            { key: "conversion", header: "Conversion", render: (row) => row.conversion },
            {
              key: "status",
              header: "Status",
              render: (row) => (
                <Badge variant={row.status === "published" ? "success" : "warning"}>{row.status}</Badge>
              ),
            },
          ]}
          rows={topPages}
        />
      </Card>

      <Card title="AI OS insights" description="Read-only — provided by the AI Content Operating System via the AI OS Bridge.">
        <p className="max-w-3xl text-sm leading-relaxed text-text-600">
          Wireframe placeholder: approved insights from the AI OS will render
          here with attribution, as read-only information. The website never
          generates, prompts, or calls AI itself — all intelligence flows
          through the AI OS Bridge.
        </p>
        <DisclosureBadge className="mt-4" text="Insights are informational only and contain no actions." />
      </Card>
    </div>
  );
}
