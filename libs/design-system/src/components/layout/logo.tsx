import { cn } from "../../lib/cn";

export interface LogoProps {
  href?: string;
  markOnly?: boolean;
  className?: string;
  size?: "sm" | "md" | "lg";
  inverse?: boolean;
}

export function Logo({
  href = "/",
  markOnly = false,
  className,
  size = "md",
  inverse = false,
}: LogoProps) {
  const shellSizeClass = size === "sm" ? "size-9" : size === "lg" ? "size-14" : "size-11";

  return (
    <a
      href={href}
      className={cn("group inline-flex items-center gap-3 transition-opacity hover:opacity-90", className)}
      aria-label="AtoZ Product Hub home"
    >
      <div className={cn("relative shrink-0 overflow-hidden rounded-[18px]", shellSizeClass)}>
        <img src="/brand/atoz-mark.svg" alt="" aria-hidden="true" className="size-full object-cover" />
      </div>
      {markOnly ? null : (
        <div className="flex flex-col">
          <span className={cn("font-serif text-base font-bold leading-none tracking-tight", inverse ? "text-surface-0" : "text-text-900")}>
            AtoZ <span className="font-normal text-primary-500">Product Hub</span>
          </span>
          <span className={cn("mt-1 text-[9px] font-semibold uppercase leading-none tracking-[0.18em]", inverse ? "text-surface-0/65" : "text-text-400")}>
            Discover · Curate · Choose Well
          </span>
        </div>
      )}
    </a>
  );
}
