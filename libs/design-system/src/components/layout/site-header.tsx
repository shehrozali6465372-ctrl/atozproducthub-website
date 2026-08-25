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
    <header className="sticky top-0 z-40 border-b border-border/70 bg-surface-0/90 backdrop-blur-md transition-colors duration-200">
      <Container className="flex h-[76px] items-center justify-between gap-4">
        <Logo size="md" />

        {/* Desktop Primary Nav */}
        <nav aria-label="Primary" className="hidden items-center lg:flex lg:absolute lg:left-1/2 lg:-translate-x-1/2">
          <ul className="flex items-center gap-1 rounded-full border border-border/50 bg-surface-1/60 p-1 backdrop-blur-xs">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <li key={item.href}>
                  <a
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "inline-flex h-9 items-center rounded-full px-4 text-xs font-semibold uppercase tracking-[0.14em] transition-all",
                      active
                        ? "bg-surface-0 text-text-900 shadow-xs ring-1 ring-border/60"
                        : "text-text-600 hover:text-text-900 hover:bg-surface-0/60",
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
            className="grid size-9 place-items-center rounded-full border border-border/50 bg-surface-1/60 text-text-600 transition-colors hover:bg-surface-2 hover:text-text-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
          >
            <Search aria-hidden="true" className="size-4" />
          </a>
          <ThemeToggle />
          <button
            type="button"
            className="grid size-9 place-items-center rounded-full border border-border/50 bg-surface-1/60 text-text-600 hover:bg-surface-2 hover:text-text-900 lg:hidden"
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
          className="border-t border-border/70 bg-surface-0/95 backdrop-blur-lg lg:hidden animate-in fade-in slide-in-from-top-2 duration-200"
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
