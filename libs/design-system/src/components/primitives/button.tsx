"use client";

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { Slot } from "@radix-ui/react-slot";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/cn";

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-primary-500 text-white hover:bg-primary-600",
  secondary: "bg-surface-2 text-text-900 hover:bg-surface-2/70",
  outline: "border border-border bg-surface-0 text-text-900 hover:bg-surface-1",
  ghost: "text-text-900 hover:bg-surface-2",
  danger: "bg-danger-500 text-white hover:bg-danger-500/90",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-9 gap-1.5 px-3 text-sm",
  md: "h-11 gap-2 px-4 text-sm",
  lg: "h-12 gap-2 px-6 text-base",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  /** Compose onto a single child (e.g. Next.js Link) via Radix Slot. */
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { variant = "primary", size = "md", loading = false, asChild = false, className, children, disabled, ...props },
    ref,
  ) => {
    const classes = cn(
      "inline-flex items-center justify-center rounded-lg font-semibold",
      "transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500",
      "disabled:pointer-events-none disabled:opacity-60",
      variantClasses[variant],
      sizeClasses[size],
      className,
    );

    if (asChild) {
      // Radix Slot requires exactly one element child; the spinner wrapper is
      // skipped so loading visuals stay a plain-button concern. `disabled`
      // was already extracted above and is not forwarded to non-button slots.
      return (
        <Slot ref={ref} className={classes} {...props}>
          {children}
        </Slot>
      );
    }

    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <Loader2 aria-hidden="true" className="size-4 animate-spin" />
        ) : null}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";

/** Small helper so TS keeps a usable type for asChild usage. */
export type ButtonContent = ReactNode;
