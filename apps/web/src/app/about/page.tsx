import type { Metadata } from "next";
import { Breadcrumbs, Container, Prose, SectionHeading } from "@atoz/design-system";

export const metadata: Metadata = {
  title: "About",
  description: "Who AtozProductHub is, what we stand for, and how we research.",
};

export default function AboutPage() {
  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs className="mb-6" items={[{ label: "Home", href: "/" }, { label: "About" }]} />
      <SectionHeading title="About AtozProductHub" description="Products worth knowing — that's the whole idea." />
      <Prose>
        <p>
          AtozProductHub is a product-discovery and content hub. We research
          products the way a helpful friend would: plainly, honestly, and with
          the details that actually matter before you spend money.
        </p>
        <h2>What we do</h2>
        <p>
          We publish articles and buying guides, and we link to products we
          recommend. When a page earns a commission, the disclosure is always
          visible — no exceptions.
        </p>
        <h2>Editorial independence</h2>
        <p>
          Recommendations are never bought. Affiliate relationships pay for
          hosting and research time; they never decide what we recommend or
          what we leave out.
        </p>
      </Prose>
    </Container>
  );
}
