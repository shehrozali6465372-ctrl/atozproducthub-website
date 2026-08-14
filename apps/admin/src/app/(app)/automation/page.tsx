import type { Metadata } from "next";
import { revalidatePath } from "next/cache";
import {
  Badge,
  Button,
  Card,
  DataTable,
  SectionHeading,
  type Column,
} from "@atoz/design-system";
import {
  createAdminApiClient,
  type AdminAutomationRule,
  type AdminExecutor,
  type AdminJobRunDetail,
  type AdminQueueItemDetail,
  type AdminScheduledJob,
} from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Automation",
  robots: { index: false, follow: false },
};

function statusVariant(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "enabled" || status === "success" || status === "done" || status === "queued") return "success";
  if (status === "pending" || status === "running" || status === "claimed" || status === "disabled") return "warning";
  if (status === "failed" || status === "cancelled") return "danger";
  return "neutral";
}

// ---------------------------------------------------------- server actions
async function enableRuleAction(formData: FormData) {
  "use server";
  const id = String(formData.get("ruleId") ?? "");
  if (id) await createAdminApiClient().automation.enableRule(id);
  revalidatePath("/automation");
}

async function disableRuleAction(formData: FormData) {
  "use server";
  const id = String(formData.get("ruleId") ?? "");
  if (id) await createAdminApiClient().automation.disableRule(id);
  revalidatePath("/automation");
}

async function runJobAction(formData: FormData) {
  "use server";
  const id = String(formData.get("jobId") ?? "");
  if (id) await createAdminApiClient().automation.runJob(id);
  revalidatePath("/automation");
}

async function retryRunAction(formData: FormData) {
  "use server";
  const id = String(formData.get("runId") ?? "");
  if (id) await createAdminApiClient().automation.retryRun(id);
  revalidatePath("/automation");
}

async function cancelRunAction(formData: FormData) {
  "use server";
  const id = String(formData.get("runId") ?? "");
  if (id) await createAdminApiClient().automation.cancelRun(id);
  revalidatePath("/automation");
}

async function retryQueueAction(formData: FormData) {
  "use server";
  const id = String(formData.get("itemId") ?? "");
  if (id) await createAdminApiClient().automation.retryQueueItem(id);
  revalidatePath("/automation");
}

async function cancelQueueAction(formData: FormData) {
  "use server";
  const id = String(formData.get("itemId") ?? "");
  if (id) await createAdminApiClient().automation.cancelQueueItem(id);
  revalidatePath("/automation");
}

// --------------------------------------------------------------- columns
const ruleColumns: Column<AdminAutomationRule>[] = [
  { key: "code", header: "Rule", render: (row) => <span className="font-medium text-text-900">{row.code}</span> },
  { key: "trigger", header: "Trigger", render: (row) => row.triggerType },
  {
    key: "status",
    header: "Status",
    render: (row) => (
      <div className="flex items-center gap-3">
        <Badge variant={statusVariant(row.status)}>{row.status}</Badge>
        <form action={row.status === "enabled" ? disableRuleAction : enableRuleAction}>
          <input type="hidden" name="ruleId" value={row.id} />
          <Button type="submit" variant="outline" size="sm">
            {row.status === "enabled" ? "Disable" : "Enable"}
          </Button>
        </form>
      </div>
    ),
  },
];

const jobColumns: Column<AdminScheduledJob>[] = [
  { key: "jobKey", header: "Job", render: (row) => <span className="font-medium text-text-900">{row.jobKey}</span> },
  { key: "cron", header: "Schedule", render: (row) => <code className="text-xs">{row.cronExpr}</code> },
  { key: "queue", header: "Queue", render: (row) => <Badge variant="neutral">{row.queue}</Badge> },
  { key: "handler", header: "Handler", render: (row) => <code className="text-xs">{row.handler}</code> },
  { key: "nextRun", header: "Next run", render: (row) => row.nextRunAt ?? "—" },
  {
    key: "actions",
    header: "Actions",
    render: (row) => (
      <form action={runJobAction}>
        <input type="hidden" name="jobId" value={row.id} />
        <Button type="submit" variant="outline" size="sm" disabled={row.status !== "enabled"}>
          Run now
        </Button>
      </form>
    ),
  },
];

const runColumns: Column<AdminJobRunDetail>[] = [
  { key: "jobKey", header: "Job", render: (row) => <code className="text-xs">{row.jobKey}</code> },
  { key: "niche", header: "Niche", render: (row) => row.nicheSlug ?? "global" },
  {
    key: "status",
    header: "Status",
    render: (row) => <Badge variant={statusVariant(row.status)}>{row.status}</Badge>,
  },
  { key: "attempts", header: "Attempts", render: (row) => String(row.attempts) },
  { key: "started", header: "Started", render: (row) => row.startedAt ?? "—" },
  { key: "error", header: "Last error", render: (row) => row.error ?? "—" },
  {
    key: "actions",
    header: "Actions",
    render: (row) => (
      <div className="flex items-center gap-2">
        {row.status === "failed" || row.status === "cancelled" ? (
          <form action={retryRunAction}>
            <input type="hidden" name="runId" value={row.id} />
            <Button type="submit" variant="outline" size="sm">
              Retry
            </Button>
          </form>
        ) : null}
        {row.status === "pending" || row.status === "running" ? (
          <form action={cancelRunAction}>
            <input type="hidden" name="runId" value={row.id} />
            <Button type="submit" variant="outline" size="sm">
              Cancel
            </Button>
          </form>
        ) : null}
      </div>
    ),
  },
];

const queueColumns: Column<AdminQueueItemDetail>[] = [
  { key: "queue", header: "Queue", render: (row) => <Badge variant="neutral">{row.queue}</Badge> },
  { key: "payload", header: "Payload", render: (row) => <code className="text-xs">{row.payloadRef}</code> },
  { key: "niche", header: "Niche", render: (row) => row.nicheSlug ?? "global" },
  {
    key: "state",
    header: "State",
    render: (row) => <Badge variant={statusVariant(row.state)}>{row.state}</Badge>,
  },
  {
    key: "attempts",
    header: "Attempts",
    render: (row) => `${row.attempts}/${row.maxAttempts}`,
  },
  { key: "error", header: "Last error", render: (row) => row.error ?? "—" },
  {
    key: "actions",
    header: "Actions",
    render: (row) => (
      <div className="flex items-center gap-2">
        {row.state === "failed" ? (
          <form action={retryQueueAction}>
            <input type="hidden" name="itemId" value={row.id} />
            <Button type="submit" variant="outline" size="sm">
              Retry
            </Button>
          </form>
        ) : null}
        {row.state === "queued" || row.state === "claimed" ? (
          <form action={cancelQueueAction}>
            <input type="hidden" name="itemId" value={row.id} />
            <Button type="submit" variant="outline" size="sm">
              Cancel
            </Button>
          </form>
        ) : null}
      </div>
    ),
  },
];

const executorColumns: Column<AdminExecutor>[] = [
  { key: "name", header: "Executor", render: (row) => <code className="text-xs">{row.name}</code> },
  { key: "queue", header: "Queue", render: (row) => <Badge variant="neutral">{row.queue}</Badge> },
];

export default async function AutomationPage() {
  const api = createAdminApiClient();
  const [rules, jobs, runs, queue, executors] = await Promise.all([
    api.automation.getRules(),
    api.automation.getJobs(),
    api.automation.getJobRuns(),
    api.automation.getQueue(),
    api.automation.getExecutors(),
  ]);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Governance"
        title="Automation"
        description="Business executors, schedules, runs and queue state — business workflows only, never AI generation."
      />

      <Card title="Rules" description="Enable or disable business automation rules.">
        <DataTable caption="Automation rules" columns={ruleColumns} rows={rules} />
      </Card>

      <Card title="Scheduled jobs" description="DB-driven cron schedules executed by the automation worker.">
        <DataTable caption="Scheduled automation jobs" columns={jobColumns} rows={jobs} />
      </Card>

      <Card title="Execution history" description="Recent job runs, retries and failures (append-only).">
        <DataTable caption="Recent automation executions" columns={runColumns} rows={runs} />
      </Card>

      <Card title="Queue ledger" description="Durable queue items with retry metadata and operator controls.">
        <DataTable caption="Automation queue ledger" columns={queueColumns} rows={queue} />
      </Card>

      <Card title="Executors" description="Registered business executors (read-only).">
        <DataTable caption="Registered executors" columns={executorColumns} rows={executors} />
      </Card>
    </div>
  );
}
