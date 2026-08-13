import type { Metadata } from "next";
import {
  Badge,
  Card,
  DataTable,
  KpiCard,
  SectionHeading,
  type Column,
} from "@atoz/design-system";
import { createAdminApiClient, type JobRunEntry, type OpsQueueItem, type ServiceStatus } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Operations",
  robots: { index: false, follow: false },
};

function statusVariant(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "ok" || status === "success" || status === "done" || status === "queued") return "success";
  if (status === "degraded" || status === "claimed" || status === "running" || status === "pending") return "warning";
  if (status === "failed" || status === "down") return "danger";
  return "neutral";
}

const queueColumns: Column<OpsQueueItem>[] = [
  { key: "queue", header: "Queue", render: (item) => <span className="font-medium">{item.queue}</span> },
  { key: "payload", header: "Payload", render: (item) => <code className="text-xs">{item.payloadRef}</code> },
  {
    key: "state",
    header: "State",
    render: (item) => <Badge variant={statusVariant(item.state)}>{item.state}</Badge>,
  },
  {
    key: "attempts",
    header: "Attempts",
    render: (item) => `${item.attempts}/${item.maxAttempts}`,
  },
  { key: "error", header: "Error", render: (item) => item.error ?? "—" },
];

const runColumns: Column<JobRunEntry>[] = [
  { key: "job", header: "Job", render: (run) => <code className="text-xs">{run.scheduledJobId}</code> },
  {
    key: "status",
    header: "Status",
    render: (run) => <Badge variant={statusVariant(run.status)}>{run.status}</Badge>,
  },
  { key: "attempts", header: "Attempts", render: (run) => String(run.attempts) },
  { key: "started", header: "Started", render: (run) => run.startedAt ?? "—" },
  { key: "error", header: "Error", render: (run) => run.error ?? "—" },
];

export default async function OperationsPage() {
  const api = createAdminApiClient();
  const [overview, systemStatus, isolation, queueItems, jobRuns] = await Promise.all([
    api.ops.getOverview(),
    api.ops.getSystemStatus(),
    api.ops.getIsolationCheck(),
    api.ops.getQueue({ limit: 10 }),
    api.ops.getJobRuns(),
  ]);

  const kpis = [
    {
      label: "Failed queue items",
      value: String(overview.failedQueueItems),
      delta: "retry via queue view",
      trend: overview.failedQueueItems > 0 ? ("down" as const) : ("flat" as const),
      hint: "Items exceeding the attempt cap need manual review",
    },
    {
      label: "Failed webhooks",
      value: String(overview.failedWebhooks),
      delta: "see logs",
      trend: overview.failedWebhooks > 0 ? ("down" as const) : ("flat" as const),
      hint: "Signature or delivery failures in the last 24h",
    },
    {
      label: "Failed operations",
      value: String(overview.failedOperations),
      delta: "see logs",
      trend: overview.failedOperations > 0 ? ("down" as const) : ("flat" as const),
      hint: "Business operations that ended in failure",
    },
    {
      label: "Open notifications",
      value: String(overview.openNotifications),
      delta: "inbox",
      trend: overview.openNotifications > 0 ? ("down" as const) : ("flat" as const),
      hint: "Unread operator notifications",
    },
  ];

  const statusColumns: Column<ServiceStatus>[] = [
    { key: "name", header: "Service", render: (svc) => <span className="font-medium">{svc.name}</span> },
    {
      key: "status",
      header: "Status",
      render: (svc) => <Badge variant={statusVariant(svc.status)}>{svc.status}</Badge>,
    },
    { key: "version", header: "Version", render: (svc) => svc.version ?? "—" },
    { key: "latency", header: "Latency", render: (svc) => (svc.latencyMs != null ? `${svc.latencyMs} ms` : "—") },
    { key: "error", header: "Error", render: (svc) => svc.error ?? "—" },
  ];

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Control plane"
        title="Operations"
        description="System health, queues, jobs, failures and tenancy isolation."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <KpiCard key={kpi.label} {...kpi} />
        ))}
      </div>

      <Card title="System status">
        <DataTable columns={statusColumns} rows={systemStatus.services} caption="Business service status" />
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Queue visibility">
          <DataTable columns={queueColumns} rows={queueItems} caption="Durable queue items" emptyLabel="No queued work" />
        </Card>
        <Card title="Recent job runs">
          <DataTable columns={runColumns} rows={jobRuns.slice(0, 8)} caption="Recent scheduled job executions" />
        </Card>
      </div>

      <Card title="Niche / account isolation">
        <p className="mb-4 text-sm text-text-600">
          {isolation.ok
            ? "No orphaned scoped records: every audit, queue, webhook and operation row references a registered niche."
            : "Orphaned scoped records detected — review the table breakdown below."}
        </p>
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {isolation.checks.map((check) => (
            <li key={check.table} className="rounded-lg border border-border p-4">
              <p className="text-sm font-semibold">{check.table}</p>
              <p className="mt-1 text-2xl font-bold">{check.rows}</p>
              <p className="mt-1 text-xs text-text-600">
                {check.orphaned.length === 0 ? "clean" : `${check.orphaned.length} orphaned`}
              </p>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
