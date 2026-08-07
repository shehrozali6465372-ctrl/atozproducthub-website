import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { EmptyState } from "../feedback/empty-state";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  cellClassName?: string;
}

export interface DataTableProps<T extends { id: string }> {
  columns: Column<T>[];
  rows: T[];
  caption?: string;
  emptyLabel?: string;
  rowKey?: (row: T) => string;
}

/**
 * Semantic table on md+; card-list layout below md (13 §15). Both views
 * render from the same data — no information is lost on small screens.
 */
export function DataTable<T extends { id: string }>({
  columns,
  rows,
  caption,
  emptyLabel = "No records",
  rowKey,
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return <EmptyState title={emptyLabel} />;
  }

  const keyOf = rowKey ?? ((row: T) => row.id);

  return (
    <div>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-sm">
          {caption ? <caption className="sr-only">{caption}</caption> : null}
          <thead>
            <tr className="border-b border-border">
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className="px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-text-400"
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => (
              <tr key={keyOf(row)} className="transition-colors hover:bg-surface-2/50">
                {columns.map((column) => (
                  <td key={column.key} className={cn("px-3 py-3 text-text-900", column.cellClassName)}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="divide-y divide-border md:hidden">
        {rows.map((row) => (
          <li key={keyOf(row)} className="py-3">
            <dl className="space-y-2">
              {columns.map((column) => (
                <div
                  key={column.key}
                  className="flex items-start justify-between gap-3 text-sm"
                >
                  <dt className="shrink-0 text-xs font-semibold uppercase tracking-wide text-text-400">
                    {column.header}
                  </dt>
                  <dd className="text-right text-text-900">{column.render(row)}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>
    </div>
  );
}
