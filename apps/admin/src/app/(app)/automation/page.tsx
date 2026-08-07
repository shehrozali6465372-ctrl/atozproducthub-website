import type { Metadata } from "next";
import {
  Badge,
  Button,
  Card,
  DataTable,
  SectionHeading,
  Switch,
} from "@atoz/design-system";
import { createAdminApiClient } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Automation",
  robots: { index: false, follow: false },
};

export default async function AutomationPage() {
  const api = createAdminApiClient();
  const rules = await api.automation.getRules();

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Governance"
        title="Automation"
        description="Business automations: schedules, runs, and failures — business workflows only, never AI generation."
        action={
          <Button variant="outline" size="sm">
            New rule
          </Button>
        }
      />
      <Card title="Rules" description="Enable or disable business automation rules.">
        <DataTable
          caption="Automation rules"
          columns={[
            { key: "name", header: "Rule", render: (row) => <span className="font-medium text-text-900">{row.name}</span> },
            { key: "schedule", header: "Schedule", render: (row) => row.schedule },
            { key: "lastRun", header: "Last run", render: (row) => row.lastRun },
            {
              key: "status",
              header: "Status",
              render: (row) => (
                <div className="flex items-center gap-3">
                  <Badge variant={row.status === "enabled" ? "success" : "neutral"}>{row.status}</Badge>
                  <Switch
                    aria-label={`Toggle ${row.name}`}
                    defaultChecked={row.status === "enabled"}
                    disabled
                  />
                </div>
              ),
            },
          ]}
          rows={rules}
        />
        <p className="mt-3 text-xs text-text-400">
          Switches are inert in M2 — rule control ships with the automation milestone.
        </p>
      </Card>
      <Card title="Run history" description="Most recent automation executions (mock).">
        <DataTable
          caption="Recent automation runs"
          columns={[
            { key: "rule", header: "Rule", render: (row) => row.rule },
            { key: "started", header: "Started", render: (row) => row.started },
            { key: "duration", header: "Duration", render: (row) => row.duration },
            {
              key: "outcome",
              header: "Outcome",
              render: (row) => (
                <Badge variant={row.outcome === "success" ? "success" : row.outcome === "failed" ? "danger" : "warning"}>
                  {row.outcome}
                </Badge>
              ),
            },
          ]}
          rows={[
            { id: "run1", rule: "Pin queue replenishment", started: "Aug 7, 06:00", duration: "1m 12s", outcome: "success" },
            { id: "run2", rule: "XML sitemap refresh", started: "Aug 7, 02:00", duration: "42s", outcome: "success" },
            { id: "run3", rule: "Affiliate reconciliation", started: "Aug 4, 04:00", duration: "5m 03s", outcome: "partial" },
            { id: "run4", rule: "Pin publishing (travelpicks)", started: "Aug 7, 18:00", duration: "8s", outcome: "failed" },
          ]}
        />
      </Card>
    </div>
  );
}
