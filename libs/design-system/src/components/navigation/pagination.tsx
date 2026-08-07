"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "../../lib/cn";
import { Button } from "../primitives/button";

export interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

/** Pagination with prev/next + numbered pages and aria-current (13 §11). */
export function Pagination({ page, totalPages, onPageChange, className }: PaginationProps) {
  return (
    <nav aria-label="Pagination" className={cn("flex flex-wrap items-center justify-between gap-4", className)}>
      <Button
        variant="outline"
        size="sm"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        <ChevronLeft aria-hidden="true" className="size-4" />
        Previous
      </Button>
      <ol className="flex flex-wrap items-center gap-1">
        {Array.from({ length: totalPages }, (_, index) => index + 1).map((p) => (
          <li key={p}>
            <button
              type="button"
              aria-current={p === page ? "page" : undefined}
              onClick={() => onPageChange(p)}
              className={cn(
                "grid size-9 place-items-center rounded-lg text-sm font-medium transition-colors",
                p === page
                  ? "bg-primary-500 text-white"
                  : "text-text-600 hover:bg-surface-2 hover:text-text-900",
              )}
            >
              {p}
            </button>
          </li>
        ))}
      </ol>
      <Button
        variant="outline"
        size="sm"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        Next
        <ChevronRight aria-hidden="true" className="size-4" />
      </Button>
    </nav>
  );
}
