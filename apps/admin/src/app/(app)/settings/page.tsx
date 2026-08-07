import type { Metadata } from "next";
import {
  Button,
  Card,
  Field,
  Input,
  SectionHeading,
  Switch,
  Textarea,
  ThemeToggle,
} from "@atoz/design-system";

export const metadata: Metadata = {
  title: "Settings",
  robots: { index: false, follow: false },
};

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Configuration"
        title="Settings"
        description="Business-layer settings. Secrets, credentials, and AI OS keys never live here — they are managed in the vault and the AI OS."
        action={
          <Button variant="outline" size="sm">
            Save changes
          </Button>
        }
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Site identity" description="Brand defaults used across the business layer.">
          <form className="space-y-5">
            <Field label="Site name" htmlFor="settings-site-name">
              <Input id="settings-site-name" defaultValue="AtozProductHub" />
            </Field>
            <Field label="Tagline" htmlFor="settings-tagline">
              <Input id="settings-tagline" defaultValue="Products worth knowing." />
            </Field>
            <Field label="Affiliate disclosure" htmlFor="settings-disclosure" hint="Shown on every monetized page.">
              <Textarea
                id="settings-disclosure"
                defaultValue="AtozProductHub participates in affiliate programs and may earn a commission from qualifying purchases."
              />
            </Field>
          </form>
        </Card>
        <div className="space-y-6">
          <Card title="Appearance">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-text-900">Color theme</p>
                <p className="text-xs text-text-600">Light / dark, persisted per operator.</p>
              </div>
              <ThemeToggle />
            </div>
          </Card>
          <Card title="Automation defaults" description="Applied to newly created rules.">
            <div className="space-y-4">
              {[
                ["Pin queue auto-replenishment", "Requeue pins when the queue drops below the threshold."],
                ["Affiliate reconciliation reminders", "Weekly digest when network payouts are due."],
              ].map(([title, description]) => (
                <div key={title} className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-text-900">{title}</p>
                    <p className="text-xs text-text-600">{description}</p>
                  </div>
                  <Switch aria-label={title} defaultChecked />
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
