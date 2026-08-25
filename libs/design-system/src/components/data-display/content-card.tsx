import { ArrowUpRight, BookOpen } from "lucide-react";
import type { ReactNode } from "react";

export interface ContentCardProps {
  title: string;
  description?: string;
  meta?: string;
  href: string;
  badge?: ReactNode;
  image?: string;
}

/** Ultra-premium editorial card with luxury image treatment, typography, and hover elevation. */
export function ContentCard({
  title,
  description,
  meta,
  href,
  badge,
  image,
}: ContentCardProps) {
  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl border border-border/70 bg-surface-0 p-3 shadow-2xs transition-all duration-300 hover:-translate-y-1 hover:border-primary-500/50 hover:shadow-lg">
      <div className="relative aspect-[16/10] w-full overflow-hidden rounded-xl bg-surface-2">
        {image ? (
          <img
            src={image}
            alt={title}
            loading="lazy"
            decoding="async"
            className="size-full object-cover transition-transform duration-500 ease-out group-hover:scale-105"
          />
        ) : (
          <div
            aria-hidden="true"
            className="flex size-full items-center justify-center bg-gradient-to-br from-surface-1 via-surface-2 to-surface-1 text-text-400"
          >
            <BookOpen className="size-8 stroke-[1.5] text-primary-500/60" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-40 transition-opacity duration-300 group-hover:opacity-20" />
        {badge ? (
          <div className="absolute top-3 left-3 shrink-0">{badge}</div>
        ) : null}
      </div>

      <div className="flex flex-1 flex-col justify-between p-3 pt-4">
        <div>
          <h3 className="font-serif text-lg font-bold leading-snug tracking-tight text-text-900 transition-colors group-hover:text-primary-500">
            <a href={href} className="focus-visible:outline-none">
              <span className="absolute inset-0" aria-hidden="true" />
              {title}
            </a>
          </h3>
          {description ? (
            <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-text-600">
              {description}
            </p>
          ) : null}
        </div>

        <div className="mt-4 flex items-center justify-between border-t border-border/40 pt-3 text-[11px] font-medium text-text-400">
          <span>{meta || "Editorial Guide"}</span>
          <span className="inline-flex items-center gap-1 font-bold uppercase tracking-widest text-text-400 transition-colors group-hover:text-text-900">
            Read <ArrowUpRight className="size-3 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </span>
        </div>
      </div>
    </article>
  );
}

