import type { Metadata } from "next";
import { Card, Logo } from "@atoz/design-system";
import { LoginForm } from "@/components/login-form";

export const metadata: Metadata = {
  title: "Login",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return (
    <main id="main-content" className="flex min-h-screen items-center justify-center bg-surface-1 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex justify-center">
          <Logo />
        </div>
        <Card title="Admin sign in" description="OIDC + MFA authentication ships in Phase 5 — this is a wireframe.">
          <LoginForm />
        </Card>
      </div>
    </main>
  );
}
