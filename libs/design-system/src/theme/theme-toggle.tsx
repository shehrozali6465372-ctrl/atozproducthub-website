"use client";

import { Moon, Sun } from "lucide-react";
import { cn } from "../lib/cn";
import { useTheme } from "./theme-provider";

/** Accessible light/dark toggle (13 §12). */
export function ThemeToggle({ label = "Toggle color theme" }: { label?: string }) {
  const { resolvedTheme, toggleTheme } = useTheme();
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={label}
      className={cn(
        "grid size-10 shrink-0 place-items-center rounded-lg text-text-600",
        "transition-colors hover:bg-surface-2 hover:text-text-900",
      )}
    >
      {resolvedTheme === "dark" ? (
        <Sun aria-hidden="true" className="size-5" />
      ) : (
        <Moon aria-hidden="true" className="size-5" />
      )}
    </button>
  );
}
