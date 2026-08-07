import type { Metadata } from "next";
import { Breadcrumbs, Container, DisclosureBadge, Prose, SectionHeading } from "@atoz/design-system";

export const metadata: Metadata = {
  title: "Affiliate Disclaimer",
  description: "AtozProductHub's affiliate and editorial disclosure.",
};

export default function DisclaimerPage() {
  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs
        className="mb-6"
        items={[{ label: "Home", href: "/" }, { label: "Disclaimer" }]}
      />
      <SectionHeading title="Affiliate & Editorial Disclaimer" description="The trust anchor for every monetized page." />
      <DisclosureBadge className="mb-6" />
      <Prose>
        <p>
          AtozProductHub participates in affiliate programs. When you click an
          affiliate link and make a purchase, we may earn a commission at no
          extra cost to you. Affiliate relationships never influence our
          recommendations.
        </p>
        <h2>Editorial independence</h2>
        <p>
          We do not accept payment for positive coverage. Products are
          recommended based on research and testing criteria documented on
          this site.
        </p>
        <h2>Your trust</h2>
        <p>
          Every monetized surface carries a visible disclosure badge. If a
          page ever misses one, tell us — corrections are part of our
          editorial process.
        </p>
      </Prose>
    </Container>
  );
}
