import type { Metadata } from "next";
import { Breadcrumbs, Card, Container, SectionHeading } from "@atoz/design-system";
import { ContactForm } from "@/components/contact/contact-form";

export const metadata: Metadata = {
  title: "Contact",
  description: "Get in touch with AtozProductHub — corrections, press, and business inquiries.",
};

export default function ContactPage() {
  return (
    <Container className="py-8 sm:py-12">
      <Breadcrumbs className="mb-6" items={[{ label: "Home", href: "/" }, { label: "Contact" }]} />
      <div className="grid gap-10 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <SectionHeading
            title="Contact us"
            description="Corrections, press, and business inquiries. We read everything, though replies can take a few days."
          />
          <p className="text-sm text-text-600">
            For affiliate-network or merchant inquiries, mention that in the
            reason field — it helps us route your message.
          </p>
        </div>
        <div className="lg:col-span-7">
          <Card title="Send a message">
            <ContactForm />
          </Card>
        </div>
      </div>
    </Container>
  );
}
