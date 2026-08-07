import type { Metadata } from "next";
import {
  Badge,
  Card,
  DataTable,
  Field,
  SectionHeading,
  Select,
} from "@atoz/design-system";
import { createAdminApiClient } from "@/lib/api-client";

export const metadata: Metadata = {
  title: "Pinterest",
  robots: { index: false, follow: false },
};

export default async function PinterestPage() {
  const api = createAdminApiClient();
  const [accounts, pinQueue] = await Promise.all([
    api.pinterest.getAccounts(),
    api.pinterest.getPinQueue(),
  ]);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Channel"
        title="Pinterest"
        description="Operate 10+ accounts, boards, and pin queues — per-account isolation is visible in every row."
      />
      <Card title="Accounts" description="Rate-limit and health indicators per account.">
        <Field label="Active account" htmlFor="pinterest-account">
          <Select id="pinterest-account" defaultValue={accounts[0]?.name}>
            {accounts.map((account) => (
              <option key={account.id} value={account.name}>
                {account.name} — {account.niche}
              </option>
            ))}
          </Select>
        </Field>
        <div className="mt-4">
          <DataTable
            caption="Pinterest accounts and health"
            columns={[
              { key: "name", header: "Account", render: (row) => <span className="font-medium text-text-900">{row.name}</span> },
              { key: "niche", header: "Niche", render: (row) => row.niche },
              { key: "boards", header: "Boards", render: (row) => row.boards },
              { key: "pins", header: "Pins", render: (row) => row.pins.toLocaleString() },
              {
                key: "rateLimit",
                header: "Rate limit",
                render: (row) => (
                  <Badge variant={row.rateLimit === "OK" ? "success" : "warning"}>{row.rateLimit}</Badge>
                ),
              },
            ]}
            rows={accounts}
          />
        </div>
      </Card>
      <Card title="Pin queue" description="Scheduled and failed pins across accounts.">
        <DataTable
          caption="Pin queue"
          columns={[
            { key: "title", header: "Pin", render: (row) => <span className="font-medium text-text-900">{row.title}</span> },
            { key: "board", header: "Board", render: (row) => row.board },
            { key: "account", header: "Account", render: (row) => <span className="font-mono text-xs">{row.account}</span> },
            { key: "scheduled", header: "Scheduled", render: (row) => row.scheduled },
            {
              key: "status",
              header: "Status",
              render: (row) => (
                <Badge variant={row.status === "scheduled" ? "info" : "danger"}>{row.status}</Badge>
              ),
            },
          ]}
          rows={pinQueue}
        />
      </Card>
    </div>
  );
}
