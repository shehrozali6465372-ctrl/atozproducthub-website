"use client";

import { useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { AdminSidebar, AdminTopbar } from "@atoz/design-system";
import { NAV_ITEMS, NOTIFICATIONS } from "@/lib/mock-data";
import { PAGE_TITLES } from "@/lib/api-client";

/** Admin app shell: sidebar (desktop) + drawer (mobile) + topbar + workspace. */
export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] ?? "Admin";

  return (
    <div className="flex min-h-screen">
      <AdminSidebar
        items={NAV_ITEMS}
        pathname={pathname}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <AdminTopbar
          title={title}
          notifications={NOTIFICATIONS}
          onMenuClick={() => setSidebarOpen(true)}
        />
        <main id="main-content" className="flex-1 p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
