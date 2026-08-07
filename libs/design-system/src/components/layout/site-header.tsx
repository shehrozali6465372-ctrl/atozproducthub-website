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

/**
 * Public site header: logo, primary navigation, theme toggle. Mobile gets a
 * hamburger drawer below lg (13 §10, §15).
 */
export function SiteHeader({
  navItems,
  pathname = "",
}: {
  navItems: NavItem[];
  pathname?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface-0/90 backdrop-blur">
      <Container className="flex h-16 items-center gap-4">
        <Logo />
        <nav aria-label="Primary" className="hidden flex-1 lg:block">
          <ul className="flex items-center gap-1">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <li key={item.href}>
                  <a
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "inline-flex h-10 items-center rounded-lg px-3 text-sm font-medium",
                      active
                        ? "bg-primary-500/10 text-primary-500"
                        : "text-text-600 hover:bg-surface-2 hover:text-text-900",
                    )}
                  >
                    {item.label}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-2">
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
          className="border-t border-border bg-surface-0 lg:hidden"
        >
          <Container className="py-3">
            <ul className="space-y-1">
              {navItems.map((item) => (
                <li key={item.href}>
                  <a
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className="block rounded-lg px-3 py-2.5 text-sm font-medium text-text-600 hover:bg-surface-2 hover:text-text-900"
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
