"use client";

import { NavRail } from "./nav-rail";
import { TopBar } from "./top-bar";
import { MobileNav } from "./mobile-nav";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-zinc-950">
      {/* NavRail is hidden on small screens, visible on md+ */}
      <div className="hidden md:block">
        <NavRail />
      </div>
      <div className="flex flex-1 flex-col md:ml-16">
        <TopBar />
        {/* Bottom padding on mobile to avoid content hidden behind MobileNav */}
        <main className="flex-1 overflow-y-auto p-3 pb-20 sm:p-4 md:p-6 md:pb-6">
          {children}
        </main>
      </div>
      {/* Mobile bottom nav — only visible on small screens */}
      <MobileNav />
    </div>
  );
}
