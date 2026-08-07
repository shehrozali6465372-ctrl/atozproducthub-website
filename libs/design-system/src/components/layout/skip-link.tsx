import { cn } from "../../lib/cn";

/** Skip-to-content link (13 §13). Target: <main id="main-content">. */
export function SkipLink({ className }: { className?: string }) {
  return (
    <a
      href="#main-content"
      className={cn(
        "sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50",
        "focus:rounded-lg focus:bg-primary-500 focus:px-4 focus:py-2 focus:font-semibold focus:text-white",
        className,
      )}
    >
      Skip to content
    </a>
  );
}
