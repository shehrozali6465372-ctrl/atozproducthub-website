"use client";

import { useState } from "react";
import { FilterBar as DesignSystemFilterBar, type FilterOption } from "@atoz/design-system";

/** Client wrapper: filter chips with local state (wireframe behavior). */
export function FilterBar({
  options,
  label,
}: {
  options: FilterOption[];
  label?: string;
}) {
  const [active, setActive] = useState<string>(options[0]?.value ?? "");
  return <DesignSystemFilterBar options={options} active={active} onChange={setActive} label={label} />;
}
