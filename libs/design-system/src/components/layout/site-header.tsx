"use client";

import { useState } from "react";
import { Menu, Search, X } from "lucide-react";
import { cn } from "../../lib/cn";
import { Container } from "./container";
import { Logo } from "./logo";
import { ThemeToggle } from "../../theme/theme-toggle";

export interface NavItem {
  label: string;
  href: string;
}

/** Premium editorial header — clean, calm, spacious with search and theme controls. */
export function SiteHeader({
  navItems,
  pathname = "",
}: {
  navItems: NavItem[];
  pathname?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-surface-0/90 backdrop-blur-xl transition-colors duration-200">
      <Container className="flex h-[80px] items-center justify-between gap-4">
        <Logo size="md" />

        {/* Desktop Primary Nav */}
        <nav aria-label="Primary" className="hidden items-center lg:flex lg:absolute lg:left-1/2 lg:-translate-x-1/2">
          <ul className="flex items-center gap-1 rounded-full border border-border/60 bg-surface-1/80 p-1 shadow-[0_12px_40px_-28px_rgba(0,0,0,0.45)] backdrop-blur">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <li key={item.href}>
                  <a
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "inline-flex h-9 items-center rounded-full px-4 text-[11px] font-semibold uppercase tracking-[0.18em] transition-all",
                      active
                        ? "bg-text-900 text-surface-0 shadow-sm ring-1 ring-text-900/10 dark:bg-surface-0 dark:text-text-900"
                        : "text-text-600 hover:bg-surface-0 hover:text-text-900",
                    )}
                  >
                    {item.label}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Action Controls */}
        <div className="ml-auto flex items-center gap-2">
          <a
            href="/search"
            aria-label="Search articles and products"
            className="grid size-10 place-items-center rounded-full border border-border/60 bg-surface-1/80 text-text-600 shadow-[0_10px_30px_-25px_rgba(0,0,0,0.5)] transition-colors hover:bg-surface-0 hover:text-text-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
          >
            <Search aria-hidden="true" className="size-4" />
          </a>
          <ThemeToggle />
          <button
            type="button"
            className="grid size-10 place-items-center rounded-full border border-border/60 bg-surface-1/80 text-text-600 shadow-[0_10px_30px_-25px_rgba(0,0,0,0.5)] hover:bg-surface-0 hover:text-text-900 lg:hidden"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close navigation" : "Open navigation"}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? (
              <X aria-hidden="true" className="size-4" />
            ) : (
              <Menu aria-hidden="true" className="size-4" />
            )}
          </button>
        </div>
      </Container>

      {/* Mobile Nav Drawer */}
      {open ? (
        <nav
          id="mobile-nav"
          aria-label="Primary"
          className="border-t border-border/70 bg-surface-0/96 backdrop-blur-xl lg:hidden animate-in fade-in slide-in-from-top-2 duration-200"
        >
          <Container className="py-5">
            <ul className="space-y-1">
              {navItems.map((item) => (
                <li key={item.href}>
                  <a
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className="flex items-center justify-between rounded-xl px-4 py-3 text-sm font-semibold tracking-wide text-text-600 hover:bg-surface-1 hover:text-text-900 transition-colors"
                  >
                    <span>{item.label}</span>
                  </a>
                </li>
              ))}
              <li className="pt-2 border-t border-border/40">
                <a
                  href="/search"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 rounded-xl px-4 py-3 text-sm font-medium text-text-600 hover:bg-surface-1 hover:text-text-900"
                >
                  <Search aria-hidden="true" className="size-4" />
                  <span>Search Products & Guides</span>
                </a>
              </li>
            </ul>
          </Container>
        </nav>
      ) : null}
    </header>
  );
}
