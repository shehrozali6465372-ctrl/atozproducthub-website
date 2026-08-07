import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export interface CardProps {
  title?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

/** Raised surface container (13 §6–§8). Titles render as section headings. */
export function Card({ title, description, action, children, className }: CardProps) {
  return (
    <section
      className={cn(
        "rounded-xl border border-border bg-surface-1 p-4 sm:p-6",
        className,
      )}
    >
      {title || action ? (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            {title ? (
              <h2 className="text-base font-semibold text-text-900">{title}</h2>
            ) : null}
            {description ? (
              <p className="mt-0.5 text-sm text-text-600">{description}</p>
            ) : null}
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
