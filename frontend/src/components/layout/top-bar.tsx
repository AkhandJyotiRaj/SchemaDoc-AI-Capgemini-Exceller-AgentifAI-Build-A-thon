"use client";

import { Activity, Wifi, WifiOff } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export function TopBar() {
  const { data: health, isError } = useQuery({
    queryKey: ["health"],
    queryFn: api.healthCheck,
    refetchInterval: 30000,
  });

  const isOnline = health && !isError;

  return (
    <header className="sticky top-0 z-30 flex h-12 items-center justify-between border-b border-zinc-800 bg-zinc-950/80 px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-zinc-100">SchemaDoc AI</h1>
        <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-blue-400">
          Beta
        </span>
      </div>

      <div className="flex items-center gap-4">
        {/* Connection Status */}
        <div className="flex items-center gap-1.5">
          {isOnline ? (
            <>
              <Wifi className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-xs text-emerald-400">Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 text-red-400" />
              <span className="text-xs text-red-400">Offline</span>
            </>
          )}
        </div>

        {/* Activity Pulse */}
        <div
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-full",
            isOnline ? "animate-pulse-ring" : "",
          )}
        >
          <Activity
            className={cn(
              "h-4 w-4",
              isOnline ? "text-blue-400" : "text-zinc-600",
            )}
          />
        </div>
      </div>
    </header>
  );
}
