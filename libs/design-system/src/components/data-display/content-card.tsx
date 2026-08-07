import { ImageIcon } from "lucide-react";
import type { ReactNode } from "react";

export interface ContentCardProps {
  title: string;
  description?: string;
  meta?: string;
  href: string;
  badge?: ReactNode;
}

/** Generic content/product card used by article, product, and pin mocks. */
export function ContentCard({ title, description, meta, href, badge }: ContentCardProps) {
  return (
    <article className="group overflow-hidden rounded-xl border border-border bg-surface-1 transition-shadow hover:shadow-md">
      <div
        aria-hidden="true"
        className="flex aspect-[16/9] items-center justify-center bg-surface-2 text-text-400"
      >
        <ImageIcon className="size-8" />
      </div>
      <div className="space-y-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-semibold text-text-900">
            <a
              href={href}
              className="rounded-sm transition-colors hover:text-primary-500 hover:underline"
            >
              {title}
            </a>
          </h3>
          {badge ? <div className="shrink-0">{badge}</div> : null}
        </div>
        {description ? (
          <p className="line-clamp-2 text-sm text-text-600">{description}</p>
        ) : null}
        {meta ? <p className="text-xs text-text-400">{meta}</p> : null}
      </div>
    </article>
  );
}
