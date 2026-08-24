"use client";

import { useState } from "react";
import { Menu, X } from "lucide-react";
import { cn } from "../../lib/cn";
import { Container } from "./container";
import { Logo } from "./logo";
import { ThemeToggle } from "../../theme/theme-toggle";

export interface NavItem {
  label: string;
  href: string;
}

/** Premium editorial header — clean, calm, spacious. */
export function SiteHeader({
  navItems,
  pathname = "",
}: {
  navItems: NavItem[];
  pathname?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b border-border/60 bg-surface-0/80 backdrop-blur-md">
      <Container className="flex h-[72px] items-center justify-between">
        <Logo />
        <nav aria-label="Primary" className="hidden items-center lg:flex lg:absolute lg:left-1/2 lg:-translate-x-1/2">
          <ul className="flex items-center gap-0.5">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <li key={item.href}>
                  <a
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "inline-flex h-10 items-center rounded-lg px-4 text-sm font-medium tracking-wide",
                      active
                        ? "text-primary-500"
                        : "text-text-600 hover:text-text-900",
                    )}
                  >
                    {item.label}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-1.5">
          <ThemeToggle />
          <button
            type="button"
            className="grid size-10 place-items-center rounded-lg text-text-600 hover:bg-surface-2 lg:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close navigation" : "Open navigation"}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? (
              <X aria-hidden="true" className="size-5" />
            ) : (
              <Menu aria-hidden="true" className="size-5" />
            )}
          </button>
        </div>
      </Container>
      {open ? (
        <nav
          id="mobile-nav"
          aria-label="Primary"
          className="border-t border-border/60 bg-surface-0 lg:hidden"
        >
          <Container className="py-4">
            <ul className="space-y-0.5">
              {navItems.map((item) => (
                <li key={item.href}>
                  <a
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className="block rounded-lg px-4 py-3 text-[15px] font-medium tracking-wide text-text-600 hover:bg-surface-2 hover:text-text-900"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </Container>
        </nav>
      ) : null}
    </header>
  );
}
