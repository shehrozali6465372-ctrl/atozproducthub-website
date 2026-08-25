import { cn } from "../../lib/cn";

export interface LogoProps {
  href?: string;
  markOnly?: boolean;
  className?: string;
  size?: "sm" | "md" | "lg";
}

/** AtoZ Product Hub — premium editorial brand mark. */
export function Logo({
  href = "/",
  markOnly = false,
  className,
  size = "md",
}: LogoProps) {
  const imgSizeClass =
    size === "sm"
      ? "size-8"
      : size === "lg"
      ? "size-12"
      : "size-9";

  return (
    <a
      href={href}
      className={cn("group inline-flex items-center gap-3 transition-opacity hover:opacity-95", className)}
      aria-label="AtoZ Product Hub home"
    >
      <div className={cn("relative shrink-0 overflow-hidden rounded-lg bg-surface-1 shadow-xs ring-1 ring-border/50", imgSizeClass)}>
        <img
          src="/brand/logo.png"
          alt="A to Z Product Hub"
          className="size-full object-cover object-center transition-transform duration-300 group-hover:scale-105"
        />
      </div>
      {markOnly ? null : (
        <div className="flex flex-col">
          <span className="font-serif text-base font-bold tracking-tight text-text-900 leading-none">
            AtoZ <span className="font-normal text-primary-500">Product Hub</span>
          </span>
          <span className="mt-1 text-[9px] font-semibold tracking-[0.18em] uppercase text-text-400 leading-none">
            Discover · Shop · Live Better
          </span>
        </div>
      )}
    </a>
  );
}
