import { BadgeCheck } from "lucide-react";
import { cn } from "../../lib/cn";

/**
 * Affiliate disclosure marker (13 §2, §5, §11). Always accompanies monetized
 * content — compliance is a display-layer responsibility, not intelligence.
 */
export function DisclosureBadge({
  text = "This page contains affiliate links. We may earn a commission if you buy — at no extra cost to you.",
  className,
}: {
  text?: string;
  className?: string;
}) {
  return (
    <p
      className={cn(
        "flex items-start gap-2 rounded-lg bg-accent-500/10 p-3 text-xs leading-relaxed text-text-600",
        className,
      )}
    >
      <BadgeCheck aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-accent-500" />
      <span>{text}</span>
    </p>
  );
}
