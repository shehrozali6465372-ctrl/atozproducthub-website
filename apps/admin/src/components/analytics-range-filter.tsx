"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FilterBar, type FilterOption } from "@atoz/design-system";

const OPTIONS: FilterOption[] = [
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last 90 days" },
  { value: "ytd", label: "Year to date" },
];

/** Server-driven date-range filter: navigates with ?range= so the analytics
 * dashboard is always rendered from real server data (M8 §5 date filters). */
export function AnalyticsRangeFilter({ active = "30d" }: { active?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  function handleChange(value: string) {
    const next = new URLSearchParams(searchParams.toString());
    if (value === "30d") next.delete("range");
    else next.set("range", value);
    router.replace(`?${next.toString()}`);
    router.refresh();
  }

  return <FilterBar options={OPTIONS} active={active} onChange={handleChange} label="Analytics range" />;
}
