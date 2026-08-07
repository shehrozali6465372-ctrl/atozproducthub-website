import type { Metadata } from "next";
import Link from "next/link";
import { Container, SectionHeading } from "@atoz/design-system";
import { SearchInput } from "@/components/search/search-input";

export const metadata: Metadata = {
  title: "Page not found",
  robots: { index: false },
};

export default function NotFound() {
  return (
    <Container className="py-16 sm:py-24">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold uppercase tracking-widest text-primary-500">
          404
        </p>
        <SectionHeading
          title="This page wandered off"
          description="The link may be out of date, or the pin you followed no longer points here. Try a search or head back to the homepage."
        />
        <div className="mx-auto max-w-md">
          <SearchInput />
        </div>
        <p className="mt-8 text-sm text-text-600">
          <Link className="font-medium text-primary-500 hover:underline" href="/">
            ← Back to homepage
          </Link>
        </p>
      </div>
    </Container>
  );
}
