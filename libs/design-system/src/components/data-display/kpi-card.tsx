import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import { cn } from "../../lib/cn";
import { Card } from "../primitives/card";

export interface KpiCardProps {
  label: string;
  value: string;
  delta?: string;
  trend?: "up" | "down" | "flat";
  hint?: string;
}

/** Dashboard KPI card: mono numerals, trend with icon + text (13 §6, §13). */
export function KpiCard({ label, value, delta, trend = "flat", hint }: KpiCardProps) {
  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  return (
    <Card className="space-y-2">
      <p className="text-sm font-medium text-text-600">{label}</p>
      <p className="font-mono text-2xl font-semibold tracking-tight text-text-900">
        {value}
      </p>
      {delta ? (
        <p
          className={cn(
            "flex items-center gap-1 text-xs font-medium",
            trend === "up"
              ? "text-success-500"
              : trend === "down"
                ? "text-danger-500"
                : "text-text-600",
          )}
        >
          <TrendIcon aria-hidden="true" className="size-3.5" />
          {delta}
          {hint ? <span className="text-text-400">· {hint}</span> : null}
        </p>
      ) : null}
    </Card>
  );
}
