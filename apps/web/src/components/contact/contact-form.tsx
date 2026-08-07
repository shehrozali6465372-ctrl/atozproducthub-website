"use client";

import { useState } from "react";
import { Button, Field, Input, Select, Textarea } from "@atoz/design-system";

/** Contact form wireframe — validation + success state only (UI-only). */
export function ContactForm() {
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | undefined>();

  if (submitted) {
    return (
      <p role="status" className="rounded-lg border border-border bg-surface-1 p-4 text-sm text-text-600">
        Thanks — your message has been received (wireframe: no message is sent
        until the contact backend ships).
      </p>
    );
  }

  return (
    <form
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        if (!data.get("email") || !data.get("message")) {
          setError("Email and message are required.");
          return;
        }
        setError(undefined);
        setSubmitted(true);
      }}
    >
      <Field label="Name" htmlFor="contact-name">
        <Input id="contact-name" name="name" autoComplete="name" />
      </Field>
      <Field label="Email" htmlFor="contact-email" required error={error?.includes("Email") ? "Email is required." : undefined}>
        <Input id="contact-email" name="email" type="email" autoComplete="email" />
      </Field>
      <Field label="Reason" htmlFor="contact-reason">
        <Select id="contact-reason" name="reason" defaultValue="general">
          <option value="general">General question</option>
          <option value="correction">Correction</option>
          <option value="business">Business / press</option>
        </Select>
      </Field>
      <Field label="Message" htmlFor="contact-message" required>
        <Textarea id="contact-message" name="message" />
      </Field>
      {error ? (
        <p role="alert" className="text-sm font-medium text-danger-500">
          {error}
        </p>
      ) : null}
      <Button type="submit">Send message</Button>
    </form>
  );
}
