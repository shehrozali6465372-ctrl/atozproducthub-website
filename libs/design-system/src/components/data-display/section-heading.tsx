import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export interface SectionHeadingProps {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  /** Heading level — one h1 per page (13 §13). */
  level?: 1 | 2 | 3;
  className?: string;
}

/** Page heading: eyebrow, title, description, optional action (13 §6). */
export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
  level = 1,
  className,
}: SectionHeadingProps) {
  const Tag = (`h${level}`) as "h1" | "h2" | "h3";
  return (
    <div className={cn("mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div className="min-w-0">
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-widest text-primary-500">
            {eyebrow}
          </p>
        ) : null}
        <Tag className="mt-1 text-2xl font-bold tracking-tight text-text-900 sm:text-3xl">
          {title}
        </Tag>
        {description ? (
          <p className="mt-1 max-w-2xl text-sm text-text-600 sm:text-base">
            {description}
          </p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
