"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  TableProperties,
  GitFork,
  MessageSquare,
  FileText,
} from "lucide-react";

/**
 * Mobile bottom navigation bar — shown only on screens smaller than md (768px).
 * Provides the same nav items as NavRail in a thumb-friendly bottom bar.
 *
 * CROSS-PLATFORM NOTE:
 * - Uses fixed positioning with safe-area-inset for iOS notch support.
 * - Tailwind responsive classes ensure it's hidden on desktop.
 */

const navItems = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/dashboard/schema", label: "Schema", icon: TableProperties },
  { href: "/dashboard/graph", label: "Graph", icon: GitFork },
  { href: "/dashboard/chat", label: "Chat", icon: MessageSquare },
  { href: "/dashboard/reports", label: "Reports", icon: FileText },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around border-t border-zinc-800 bg-zinc-950/95 backdrop-blur-sm pb-[env(safe-area-inset-bottom)] md:hidden">
      {navItems.map((item) => {
        const isActive =
          item.href === "/dashboard"
            ? pathname === "/dashboard"
            : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-0.5 px-3 py-2 text-[10px] font-medium transition-colors",
              isActive ? "text-blue-400" : "text-zinc-500 active:text-zinc-300",
            )}
          >
            <item.icon className="h-5 w-5" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
