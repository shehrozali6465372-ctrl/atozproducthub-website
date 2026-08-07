import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "min-h-28 w-full rounded-lg border border-border bg-surface-0 px-3 py-2 text-sm text-text-900",
        "placeholder:text-text-400 transition-colors",
        "focus:border-primary-500 focus:outline-none",
        "disabled:opacity-60 aria-invalid:border-danger-500",
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";
