import type { ReactNode } from "react";
import { Card } from "../primitives/card";

export interface ChartCardProps {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  /** Screen-reader-visible data table fallback (13 §12, §13). */
  srTable?: ReactNode;
  className?: string;
}

/** Dashboard chart wrapper: card + chart + accessible data-table fallback. */
export function ChartCard({ title, description, action, children, srTable, className }: ChartCardProps) {
  return (
    <Card title={title} description={description} action={action} className={className}>
      <div className="h-64 w-full">{children}</div>
      {srTable ? <div className="sr-only">{srTable}</div> : null}
    </Card>
  );
}
