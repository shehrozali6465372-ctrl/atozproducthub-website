import { Menu } from "lucide-react";
import { Avatar } from "../data-display/avatar";
import { SearchInput } from "../forms/search-input";
import { NotificationBell, type NotificationItem } from "../feedback/notifications";

/** Admin app-shell topbar: menu (mobile), search, notifications, avatar. */
export function AdminTopbar({
  title,
  notifications,
  onMenuClick,
}: {
  title: string;
  notifications: NotificationItem[];
  onMenuClick: () => void;
}) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-surface-0/90 px-4 backdrop-blur sm:px-6">
      <button
        type="button"
        onClick={onMenuClick}
        aria-label="Open navigation"
        className="grid size-10 shrink-0 place-items-center rounded-lg text-text-600 hover:bg-surface-2 lg:hidden"
      >
        <Menu aria-hidden="true" className="size-5" />
      </button>
      <h1 className="min-w-0 flex-1 truncate text-base font-semibold text-text-900">
        {title}
      </h1>
      <SearchInput aria-label="Search admin" className="hidden w-64 md:block" />
      <NotificationBell notifications={notifications} />
      <Avatar name="Admin User" />
    </header>
  );
}
