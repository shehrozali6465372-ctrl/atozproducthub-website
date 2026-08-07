"use client";

import { useState } from "react";
import { Button, Field, Input } from "@atoz/design-system";

/** Login wireframe — UI only; real OIDC/MFA flow arrives in Phase 5. */
export function LoginForm() {
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  return (
    <form
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        if (!data.get("email")) {
          setError("Email is required.");
          return;
        }
        setError(undefined);
        setLoading(true);
        // No authentication exists in M2 — the flow terminates here on purpose.
        setTimeout(() => setLoading(false), 400);
      }}
    >
      <Field label="Email" htmlFor="login-email" required error={error}>
        <Input id="login-email" name="email" type="email" autoComplete="email" placeholder="admin@atozproducthub.com" />
      </Field>
      <Field label="Password" htmlFor="login-password">
        <Input id="login-password" name="password" type="password" autoComplete="current-password" placeholder="••••••••" />
      </Field>
      <Button type="submit" className="w-full" loading={loading}>
        Sign in
      </Button>
      <p className="text-center text-xs text-text-400">
        Wireframe only — sign-in does not authenticate in M2.
      </p>
    </form>
  );
}
