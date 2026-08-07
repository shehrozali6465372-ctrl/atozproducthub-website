import { cn } from "../../lib/cn";

export interface LogoProps {
  href?: string;
  markOnly?: boolean;
  className?: string;
}

/** Wordmark + discovery mark (13 §2). Text is brand-owned, not a final asset. */
export function Logo({ href = "/", markOnly = false, className }: LogoProps) {
  return (
    <a
      href={href}
      className={cn("inline-flex items-center gap-2 rounded-md", className)}
      aria-label="AtozProductHub home"
    >
      <span
        aria-hidden="true"
        className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary-500 text-sm font-bold text-white"
      >
        A
      </span>
      {markOnly ? null : (
        <span className="text-lg font-bold tracking-tight text-text-900">
          AtozProductHub
        </span>
      )}
    </a>
  );
}
