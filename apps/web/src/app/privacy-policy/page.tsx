import type { Metadata } from "next";
import { Breadcrumbs, Container, Prose, SectionHeading } from "@atoz/design-system";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How AtozProductHub handles data, cookies, and consent.",
};

export default function PrivacyPolicyPage() {
  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs
        className="mb-6"
        items={[{ label: "Home", href: "/" }, { label: "Privacy Policy" }]}
      />
      <SectionHeading title="Privacy Policy" description="Last updated: August 7, 2026 (placeholder copy — legal review required)." />
      <Prose>
        <p>
          This page explains what information AtozProductHub collects, why we
          collect it, and the choices you have. It is placeholder text for the
          wireframe milestone and must be finalized with legal review before
          launch.
        </p>
        <h2>What we collect</h2>
        <p>Standard web analytics, referral data from Pinterest, and affiliate
        click attribution necessary to operate the business layer.</p>
        <h2>Cookies</h2>
        <p>Affiliate and analytics tracking cookies are disclosed and subject
        to consent controls described here once the consent banner ships.</p>
        <h2>Your choices</h2>
        <p>Opt-out links, deletion requests, and contact details will live here
        in the final version.</p>
      </Prose>
    </Container>
  );
}
