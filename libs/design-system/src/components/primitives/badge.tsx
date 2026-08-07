import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export type BadgeVariant = "neutral" | "success" | "warning" | "danger" | "info" | "accent";

const variantClasses: Record<BadgeVariant, string> = {
  neutral: "bg-surface-2 text-text-600",
  success: "bg-success-500/15 text-success-500",
  warning: "bg-warning-500/15 text-warning-500",
  danger: "bg-danger-500/15 text-danger-500",
  info: "bg-info-500/15 text-info-500",
  accent: "bg-accent-500/15 text-accent-500",
};

export interface BadgeProps {
  variant?: BadgeVariant;
  icon?: ReactNode;
  children?: ReactNode;
  className?: string;
}

/** Status / label badge. Status is never color-only (paired with text/icon). */
export function Badge({ variant = "neutral", icon, children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        variantClasses[variant],
        className,
      )}
    >
      {icon ? <span aria-hidden="true">{icon}</span> : null}
      {children ?? null}
    </span>
  );
}
