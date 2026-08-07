"use client";

import { useState, type InputHTMLAttributes } from "react";
import { Search } from "lucide-react";
import { cn } from "../../lib/cn";
import { Input } from "./input";

export interface SearchInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "onSubmit"> {
  onSubmit?: (value: string) => void;
  label?: string;
}

/** Accessible search box: role=search, icon, Enter-to-submit (13 §11). */
export function SearchInput({ onSubmit, label = "Search", className, ...props }: SearchInputProps) {
  const [value, setValue] = useState("");

  return (
    <form
      role="search"
      className={cn("relative", className)}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit?.(value);
      }}
    >
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-text-400"
      />
      <Input
        aria-label={label}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        className="pl-10"
        {...props}
      />
      <button type="submit" className="sr-only">
        Submit search
      </button>
    </form>
  );
}
