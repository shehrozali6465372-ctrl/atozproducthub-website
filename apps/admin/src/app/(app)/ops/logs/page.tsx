import type { Metadata } from "next";
import { Badge, Card, DataTable, SectionHeading, type Column } from "@atoz/design-system";
import {
  createAdminApiClient,
  type OperationLogEntry,
  type WebhookLogEntry,
} from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Operations logs",
  robots: { index: false, follow: false },
};

function statusVariant(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "succeeded" || status === "processed") return "success";
  if (status === "started" || status === "received") return "warning";
  if (status === "failed" || status === "ignored") return "danger";
  return "neutral";
}

const operationColumns: Column<OperationLogEntry>[] = [
  {
    key: "operation",
    header: "Operation",
    render: (entry) => <span className="font-medium">{entry.operation}</span>,
  },
  {
    key: "status",
    header: "Status",
    render: (entry) => <Badge variant={statusVariant(entry.status)}>{entry.status}</Badge>,
  },
  { key: "entity", header: "Entity", render: (entry) => `${entry.entityType} ${entry.entityId}` },
  { key: "message", header: "Message", render: (entry) => entry.message },
  { key: "niche", header: "Niche", render: (entry) => (entry.nicheId ? <code className="text-xs">{entry.nicheId}</code> : "global") },
  { key: "occurred", header: "Occurred", render: (entry) => new Date(entry.occurredAt).toLocaleString() },
];

const webhookColumns: Column<WebhookLogEntry>[] = [
  { key: "source", header: "Source", render: (entry) => <span className="font-medium">{entry.source}</span> },
  { key: "event", header: "Event", render: (entry) => <code className="text-xs">{entry.eventId}</code> },
  {
    key: "status",
    header: "Status",
    render: (entry) => <Badge variant={statusVariant(entry.status)}>{entry.status}</Badge>,
  },
  { key: "niche", header: "Niche", render: (entry) => (entry.nicheId ? <code className="text-xs">{entry.nicheId}</code> : "global") },
  { key: "error", header: "Error", render: (entry) => entry.error ?? "—" },
  { key: "received", header: "Received", render: (entry) => new Date(entry.receivedAt).toLocaleString() },
];

export default async function OperationsLogsPage() {
  const api = createAdminApiClient();
  const [operations, webhooks] = await Promise.all([
    api.ops.getOperationLogs({ limit: 50 }),
    api.ops.getWebhookLogs({ limit: 50 }),
  ]);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Control plane"
        title="Operations logs"
        description="Searchable operation records and webhook delivery history (including failures)."
      />

      <Card title="Operation log">
        <DataTable columns={operationColumns} rows={operations} caption="Recent business operations" />
      </Card>

      <Card title="Webhook deliveries">
        <DataTable columns={webhookColumns} rows={webhooks} caption="Recent webhook deliveries" emptyLabel="No webhook deliveries" />
      </Card>
    </div>
  );
}
