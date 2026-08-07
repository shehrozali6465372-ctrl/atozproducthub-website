import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

/** Long-form article typography: Lora serif, 72–78 char measure (13 §4, §14). */
export function Prose({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "max-w-[72ch] font-serif text-[1.0625rem] leading-7 text-text-900 sm:text-[1.1875rem]",
        "[&_h2]:mt-10 [&_h2]:mb-3 [&_h2]:font-sans [&_h2]:text-xl [&_h2]:font-bold [&_h2]:text-text-900",
        "[&_h3]:mt-8 [&_h3]:mb-2 [&_h3]:font-sans [&_h3]:text-lg [&_h3]:font-semibold [&_h3]:text-text-900",
        "[&_p]:mb-6 [&_ul]:mb-6 [&_ul]:list-disc [&_ul]:pl-6 [&_ol]:mb-6 [&_ol]:list-decimal [&_ol]:pl-6",
        "[&_li]:mb-2 [&_a]:text-primary-500 [&_a]:underline",
        className,
      )}
    >
      {children}
    </div>
  );
}
