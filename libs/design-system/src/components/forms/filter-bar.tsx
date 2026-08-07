"use client";

import { cn } from "../../lib/cn";

export interface FilterOption {
  value: string;
  label: string;
}

/**
 * Inline filter chips; collapsible-drawer behavior for < lg is a later
 * enhancement (13 §10). aria-pressed conveys active state.
 */
export function FilterBar({
  options,
  active,
  onChange,
  label = "Filters",
}: {
  options: FilterOption[];
  active?: string;
  onChange: (value: string) => void;
  label?: string;
}) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap items-center gap-2">
      {options.map((option) => {
        const isActive = active === option.value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(option.value)}
            className={cn(
              "h-9 rounded-full border px-3.5 text-sm font-medium transition-colors",
              isActive
                ? "border-primary-500 bg-primary-500/10 text-primary-500"
                : "border-border bg-surface-0 text-text-600 hover:bg-surface-1 hover:text-text-900",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
