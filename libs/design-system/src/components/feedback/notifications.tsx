"use client";

import { useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { cn } from "../../lib/cn";
import { Badge, type BadgeVariant } from "../primitives/badge";

export interface NotificationItem {
  id: string;
  title: string;
  description?: string;
  timestamp: string;
  tone?: BadgeVariant;
  read?: boolean;
}

/** Notification bell with unread count and popover list (13 §11, §13). */
export function NotificationBell({
  notifications,
  label = "Notifications",
}: {
  notifications: NotificationItem[];
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const unread = notifications.filter((item) => !item.read).length;

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-label={`${label} (${unread} unread)`}
        aria-expanded={open}
        aria-haspopup="true"
        onClick={() => setOpen((value) => !value)}
        className="relative grid size-10 place-items-center rounded-lg text-text-600 transition-colors hover:bg-surface-2 hover:text-text-900"
      >
        <Bell aria-hidden="true" className="size-5" />
        {unread > 0 ? (
          <span className="absolute right-1 top-1 grid size-4 place-items-center rounded-full bg-danger-500 text-[10px] font-bold text-white">
            {unread}
          </span>
        ) : null}
      </button>
      {open ? (
        <div className="absolute right-0 z-40 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-border bg-surface-0 shadow-lg">
          <p className="border-b border-border px-4 py-3 text-sm font-semibold text-text-900">
            {label}
          </p>
          {notifications.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-text-600">
              You're all caught up.
            </p>
          ) : (
            <ul className="max-h-96 divide-y divide-border overflow-auto">
              {notifications.map((item) => (
                <li key={item.id} className="flex gap-3 px-4 py-3">
                  <Badge variant={item.tone ?? "info"} />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-text-900">{item.title}</p>
                    {item.description ? (
                      <p className="mt-0.5 text-xs text-text-600">{item.description}</p>
                    ) : null}
                    <time className="mt-0.5 block text-xs text-text-400">
                      {item.timestamp}
                    </time>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}

export interface Toast {
  id: string;
  title: string;
  description?: string;
  tone?: BadgeVariant;
}

/** Live toast region — role=status announcements (13 §13). */
export function ToastRegion({
  toasts = [],
  label = "Notifications",
}: {
  toasts?: Toast[];
  label?: string;
}) {
  return (
    <div
      aria-label={label}
      role="region"
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className={cn(
            "pointer-events-auto rounded-lg border border-border bg-surface-0 p-4 shadow-lg",
          )}
        >
          <div className="flex items-start gap-3">
            <Badge variant={toast.tone ?? "info"} />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-text-900">{toast.title}</p>
              {toast.description ? (
                <p className="mt-0.5 text-xs text-text-600">{toast.description}</p>
              ) : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
