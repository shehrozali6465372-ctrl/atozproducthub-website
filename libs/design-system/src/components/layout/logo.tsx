import { cn } from "../../lib/cn";

export interface LogoProps {
  href?: string;
  markOnly?: boolean;
  className?: string;
  size?: "sm" | "md" | "lg";
  inverse?: boolean;
}

/** AtoZ Product Hub — premium editorial brand mark. */
export function Logo({
  href = "/",
  markOnly = false,
  className,
  size = "md",
  inverse = false,
}: LogoProps) {
  const shellSizeClass =
    size === "sm"
      ? "size-9"
      : size === "lg"
      ? "size-14"
      : "size-11";

  return (
    <a
      href={href}
      className={cn("group inline-flex items-center gap-3 transition-opacity hover:opacity-95", className)}
      aria-label="AtoZ Product Hub home"
    >
      <div
        className={cn(
          "relative shrink-0 overflow-hidden rounded-2xl border shadow-[0_10px_30px_-20px_rgba(0,0,0,0.4)]",
          inverse ? "border-white/10 bg-white/5" : "border-border/70 bg-surface-1",
          shellSizeClass,
        )}
      >
        <div className="absolute inset-0 editorial-grid opacity-60" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_24%,rgba(164,119,82,0.18),transparent_34%),radial-gradient(circle_at_70%_72%,rgba(17,17,17,0.08),transparent_34%)]" />
        <div className="absolute inset-x-4 top-1/2 h-px -translate-y-1/2 bg-current/10" />
        <div className={cn(
          "absolute left-2.5 top-2.5 rounded-full px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-[0.28em]",
          inverse ? "bg-white/10 text-surface-0/75" : "bg-surface-0/80 text-text-400",
        )}>
          A
        </div>
        <div className={cn(
          "absolute bottom-2.5 right-2.5 rounded-full px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-[0.28em]",
          inverse ? "bg-surface-0 text-text-900" : "bg-text-900 text-surface-0",
        )}>
          Z
        </div>
        <div className="absolute inset-0 grid place-items-center">
          <span className={cn(
            "font-serif text-[20px] font-bold leading-none",
            inverse ? "text-surface-0" : "text-text-900",
          )}>
            A
          </span>
        </div>
        <div className="absolute inset-0 grid place-items-center">
          <span className="mt-3 text-[10px] font-semibold uppercase tracking-[0.45em] text-primary-500">
            •
          </span>
        </div>
      </div>
      {markOnly ? null : (
        <div className="flex flex-col">
          <span
            className={cn(
              "font-serif text-base font-bold tracking-tight leading-none",
              inverse ? "text-surface-0" : "text-text-900",
            )}
          >
            AtoZ <span className="font-normal text-primary-500">Product Hub</span>
          </span>
          <span className={cn(
            "mt-1 text-[9px] font-semibold leading-none uppercase tracking-[0.18em]",
            inverse ? "text-surface-0/70" : "text-text-400",
          )}>
            Discover · Curate · Live Better
          </span>
        </div>
      )}
    </a>
  );
}
