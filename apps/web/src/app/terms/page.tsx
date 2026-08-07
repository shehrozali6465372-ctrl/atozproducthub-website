import type { Metadata } from "next";
import { Breadcrumbs, Container, Prose, SectionHeading } from "@atoz/design-system";

export const metadata: Metadata = {
  title: "Terms of Use",
  description: "The terms that govern use of the AtozProductHub website.",
};

export default function TermsPage() {
  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs className="mb-6" items={[{ label: "Home", href: "/" }, { label: "Terms" }]} />
      <SectionHeading title="Terms of Use" description="Last updated: August 7, 2026 (placeholder copy — legal review required)." />
      <Prose>
        <p>
          These terms govern your use of the AtozProductHub website.
          Placeholder text for the wireframe milestone; final terms require
          legal review before launch.
        </p>
        <h2>Content</h2>
        <p>Articles and guides are provided for general information and do not
        constitute professional advice.</p>
        <h2>Affiliate links</h2>
        <p>Some pages contain affiliate links. Purchases through those links
        may earn us a commission at no additional cost to you, as detailed on
        the disclaimer page.</p>
        <h2>Acceptable use</h2>
        <p>Automated scraping, reselling of content, and interference with the
        website are not permitted.</p>
      </Prose>
    </Container>
  );
}
