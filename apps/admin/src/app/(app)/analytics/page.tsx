import type { Metadata } from "next";
import {
  Badge,
  Card,
  ChartCard,
  DataTable,
  DonutChartView,
  KpiCard,
  LineChartView,
  SectionHeading,
} from "@atoz/design-system";
import { createAdminApiClient } from "@/lib/api-client";
import { AnalyticsRangeFilter } from "@/components/analytics-range-filter";

export const metadata: Metadata = {
  title: "Analytics",
  robots: { index: false, follow: false },
};

const RANGES: Record<string, { days: number; startOfYear: boolean }> = {
  "30d": { days: 30, startOfYear: false },
  "90d": { days: 90, startOfYear: false },
  ytd: { days: 0, startOfYear: true },
};

function rangeDates(range: string): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  const spec = RANGES[range] ?? RANGES["30d"];
  if (spec.startOfYear) {
    from.setMonth(0, 1);
  } else {
    from.setDate(to.getDate() - spec.days);
  }
  const iso = (date: Date) => date.toISOString().slice(0, 10);
  return { from: iso(from), to: iso(to) };
}

export default async function AnalyticsPage({
  searchParams,
}: {
  searchParams: Promise<{ range?: string }>;
}) {
  const { range } = await searchParams;
  const { from, to } = rangeDates(range ?? "30d");
  const api = createAdminApiClient();
  const [overview, trafficSeries, trafficSources, topPages, metricSeries] = await Promise.all([
    api.analytics.getOverview(from, to),
    api.analytics.getTrafficSeries(from, to),
    api.analytics.getTrafficSources(from, to),
    api.analytics.getTopPages(from, to),
    api.analytics.getMetricSeries(from, to),
  ]);

  const revenueByDate = new Map<string, number>();
  const clicksByDate = new Map<string, number>();
  const conversionsByDate = new Map<string, number>();
  for (const point of metricSeries) {
    const target =
      point.metricKey === "revenue.amount"
        ? revenueByDate
        : point.metricKey === "affiliate.clicks"
          ? clicksByDate
          : point.metricKey === "conversions"
            ? conversionsByDate
            : null;
    if (target) target.set(point.date, point.value);
  }
  const metricChart = [...new Set([...revenueByDate.keys(), ...clicksByDate.keys(), ...conversionsByDate.keys()])]
    .sort()
    .map((date) => ({
      label: date,
      clicks: clicksByDate.get(date) ?? 0,
      conversions: conversionsByDate.get(date) ?? 0,
      revenue: revenueByDate.get(date) ?? 0,
    }));

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Measurement"
        title="Analytics"
        description="Traffic, engagement, and conversion — first-party events, append-only ledger, and niche-scoped read models (M8)."
      />
      <AnalyticsRangeFilter active={range ?? "30d"} />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Sessions" value={overview.sessions.toLocaleString()} delta="30d" hint="all sources" />
        <KpiCard label="Pageviews" value={overview.pageviews.toLocaleString()} delta="30d" hint="all pages" />
        <KpiCard label="Unique visitors" value={overview.uniqueVisitors.toLocaleString()} delta="30d" hint="users" />
        <KpiCard label="Bounce rate" value={`${(overview.bounceRate * 100).toFixed(1)}%`} delta="30d" hint="avg" />
        <KpiCard label="Affiliate clicks" value={overview.affiliateClicks.toLocaleString()} delta="30d" hint="clicks" />
        <KpiCard label="Conversions" value={overview.conversions.toLocaleString()} delta="30d" hint="sales" />
        <KpiCard label="Revenue" value={`$${overview.revenueAmount.toLocaleString(undefined, { maximumFractionDigits: 2 })}`} delta="30d" hint="attributed" />
        <KpiCard label="Pin clicks" value={overview.pinClicks.toLocaleString()} delta="30d" hint="pinterest" />
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard
          title="Sessions over time"
          description="Weekly sessions by source"
          className="lg:col-span-2"
          srTable={
            <table>
              <caption>Weekly sessions by source</caption>
              <tbody>
                {trafficSeries.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    <td>{row.pinterest + row.organic + row.direct + row.other}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          }
        >
          <LineChartView
            data={trafficSeries.map((row) => ({
              ...row,
              sessions: row.pinterest + row.organic + row.direct + row.other,
            }))}
            series={[{ key: "sessions", name: "Sessions", color: "var(--color-primary-500)" }]}
            ariaLabel="Sessions over the selected range"
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
      <ChartCard
        title="Affiliate & revenue metrics"
        description="Clicks, conversions, and attributed revenue over the selected range"
        srTable={
          <table>
            <caption>Affiliate and revenue metrics by day</caption>
            <tbody>
              {metricChart.map((row) => (
                <tr key={row.label}>
                  <th scope="row">{row.label}</th>
                  <td>{row.clicks} clicks</td>
                  <td>{row.conversions} conversions</td>
                  <td>${row.revenue.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      >
        <LineChartView
          data={metricChart}
          series={[
            { key: "clicks", name: "Clicks", color: "var(--color-primary-500)" },
            { key: "conversions", name: "Conversions", color: "var(--color-success-500)" },
            { key: "revenue", name: "Revenue ($)", color: "var(--color-danger-500)" },
          ]}
          ariaLabel="Affiliate clicks, conversions, and revenue over the selected range"
        />
      </ChartCard>
      <Card title="Top pages" description="Highest-traffic pages this period.">
        <DataTable
          caption="Top pages by pageviews"
          columns={[
            { key: "path", header: "Page", render: (row) => <span className="font-medium text-primary-500">{row.path}</span> },
            { key: "visits", header: "Pageviews", render: (row) => row.visits.toLocaleString() },
            { key: "uniqueVisitors", header: "Unique visitors", render: (row) => row.uniqueVisitors.toLocaleString() },
            {
              key: "conversion",
              header: "Pageviews / visitor",
              render: (row) => <Badge variant={row.conversion === "—" ? "neutral" : "success"}>{row.conversion}</Badge>,
            },
          ]}
          rows={topPages}
        />
      </Card>
    </div>
  );
}
