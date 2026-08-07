"use client";

import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/cn";
import { Logo } from "./logo";

export interface AdminNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  section: string;
}

/**
 * Admin app-shell sidebar: icon navigation, active state, mobile drawer
 * below lg (13 §6 admin archetype, §15). Receives pathname as a prop to stay
 * framework-agnostic.
 */
export function AdminSidebar({
  items,
  pathname = "",
  isOpen,
  onClose,
}: {
  items: AdminNavItem[];
  pathname?: string;
  isOpen: boolean;
  onClose: () => void;
}) {
  const sections = [...new Set(items.map((item) => item.section))];

  return (
    <>
      {isOpen ? (
        <div
          aria-hidden="true"
          onClick={onClose}
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
        />
      ) : null}
      <aside
        id="admin-sidebar"
        aria-label="Admin navigation"
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 -translate-x-full border-r border-border bg-surface-1",
          "transition-transform duration-200 lg:static lg:z-auto lg:translate-x-0",
          isOpen && "translate-x-0",
        )}
      >
        <div className="flex h-full flex-col">
          <div className="flex h-16 shrink-0 items-center border-b border-border px-4">
            <Logo />
          </div>
          <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
            {sections.map((section) => (
              <div key={section}>
                <p className="px-3 pb-2 text-xs font-semibold uppercase tracking-widest text-text-400">
                  {section}
                </p>
                <ul className="space-y-1">
                  {items
                    .filter((item) => item.section === section)
                    .map((item) => {
                      const active =
                        pathname === item.href ||
                        (item.href !== "/" && pathname.startsWith(item.href));
                      return (
                        <li key={item.href}>
                          <a
                            href={item.href}
                            aria-current={active ? "page" : undefined}
                            onClick={onClose}
                            className={cn(
                              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium",
                              active
                                ? "bg-primary-500/10 text-primary-500"
                                : "text-text-600 hover:bg-surface-2 hover:text-text-900",
                            )}
                          >
                            <item.icon aria-hidden="true" className="size-5 shrink-0" />
                            {item.label}
                          </a>
                        </li>
                      );
                    })}
                </ul>
              </div>
            ))}
          </nav>
          <div className="border-t border-border p-3">
            <a
              href="/login"
              className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-text-600 hover:bg-surface-2 hover:text-text-900"
            >
              <span aria-hidden="true">←</span> Back to login
            </a>
          </div>
        </div>
      </aside>
    </>
  );
}
