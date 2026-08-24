import { cn } from "../../lib/cn";

export interface LogoProps {
  href?: string;
  markOnly?: boolean;
  className?: string;
}

/** AtoZ Product Hub — premium editorial brand mark. */
export function Logo({ href = "/", markOnly = false, className }: LogoProps) {
  return (
    <a
      href={href}
      className={cn("inline-flex items-center gap-2.5", className)}
      aria-label="AtoZ Product Hub home"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 36 36"
        fill="none"
        className="size-9 shrink-0"
      >
        <rect width="36" height="36" rx="8" className="fill-[#171717] dark:fill-[#faf9f6]" />
        <text x="7" y="24" fontSize="15" fontWeight="700" fontFamily="Georgia, serif" className="fill-[#faf9f6] dark:fill-[#171717]" letterSpacing="-0.5">A</text>
        <path d="M18 10 L26 26" stroke="#c8a96b" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M22 22 L26 26 L21 25" stroke="#c8a96b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <text x="23" y="30" fontSize="11" fontWeight="600" fontFamily="Georgia, serif" fill="#c8a96b">Z</text>
      </svg>
      {markOnly ? null : (
        <span className="flex flex-col leading-none">
          <span className="text-base font-bold tracking-tight text-text-900">
            AtoZ <span className="font-normal text-primary-500">Product Hub</span>
          </span>
        </span>
      )}
    </a>
  );
}
