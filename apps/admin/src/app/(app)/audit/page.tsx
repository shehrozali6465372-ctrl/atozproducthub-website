import type { Metadata } from "next";
import { Badge, Card, DataTable, SectionHeading, type Column } from "@atoz/design-system";
import { createAdminApiClient, type AuditEntry } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Audit",
  robots: { index: false, follow: false },
};

const columns: Column<AuditEntry>[] = [
  {
    key: "action",
    header: "Action",
    render: (entry) => <Badge variant="neutral">{entry.action}</Badge>,
  },
  { key: "entity", header: "Entity", render: (entry) => (
    <span className="font-medium">{entry.entityType}</span>
  ) },
  { key: "entityId", header: "Entity ID", render: (entry) => <code className="text-xs">{entry.entityId}</code> },
  { key: "actor", header: "Actor", render: (entry) => entry.adminUserId ?? "system" },
  { key: "niche", header: "Niche", render: (entry) => (entry.nicheId ? <code className="text-xs">{entry.nicheId}</code> : "global") },
  { key: "request", header: "Request ID", render: (entry) => entry.requestId ?? "—" },
  { key: "occurred", header: "Occurred", render: (entry) => new Date(entry.occurredAt).toLocaleString() },
];

export default async function AuditPage() {
  const api = createAdminApiClient();
  const entries = await api.ops.getAudit({ limit: 50 });

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Governance"
        title="Audit log"
        description="Append-only record of every privileged action — immutable, searchable, exportable."
      />
      <Card title="Latest audit entries">
        <DataTable columns={columns} rows={entries} caption="Recent audit records" />
      </Card>
    </div>
  );
}
