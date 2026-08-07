"use client";

import { useRouter } from "next/navigation";
import { SearchInput as DesignSystemSearchInput } from "@atoz/design-system";

/** Client wrapper: submits to the /search route (wireframe behavior). */
export function SearchInput({ placeholder = "Search articles and products…" }: { placeholder?: string }) {
  const router = useRouter();
  return (
    <DesignSystemSearchInput
      placeholder={placeholder}
      onSubmit={(value) => router.push(`/search?q=${encodeURIComponent(value)}`)}
    />
  );
}
