import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-11 w-full rounded-lg border border-border bg-surface-0 px-3 text-sm text-text-900",
        "placeholder:text-text-400 transition-colors",
        "focus:border-primary-500 focus:outline-none",
        "disabled:opacity-60 aria-invalid:border-danger-500",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
