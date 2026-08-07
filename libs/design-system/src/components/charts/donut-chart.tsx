"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { cn } from "../../lib/cn";

export interface DonutDatum {
  name: string;
  value: number;
  color: string;
}

/** Accessible donut chart (Recharts) using design tokens. */
export function DonutChartView({
  data,
  ariaLabel,
  className,
}: {
  data: DonutDatum[];
  ariaLabel: string;
  className?: string;
}) {
  return (
    <div role="img" aria-label={ariaLabel} className={cn("h-full w-full", className)}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius="55%"
            outerRadius="80%"
            paddingAngle={2}
            stroke="var(--color-surface-0)"
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--color-surface-1)",
              border: "1px solid var(--color-border)",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelStyle={{ color: "var(--color-text-900)" }}
          />
          <Legend
            formatter={(value) => (
              <span style={{ color: "var(--color-text-600)", fontSize: 12 }}>
                {value}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
