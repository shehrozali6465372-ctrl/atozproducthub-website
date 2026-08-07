import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

/** Max-width 1200px page container with responsive gutters (13 §6–§8). */
export function Container({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mx-auto w-full max-w-[1200px] px-4 sm:px-6 lg:px-8", className)}>
      {children}
    </div>
  );
}
