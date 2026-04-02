import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  return num.toLocaleString();
}

export function healthColor(score: number): string {
  if (score >= 90) return "text-green-400";
  if (score >= 70) return "text-amber-400";
  return "text-red-400";
}

export function healthBgColor(score: number): string {
  if (score >= 90) return "bg-green-500/15";
  if (score >= 70) return "bg-amber-500/15";
  return "bg-red-500/15";
}

export function healthBarHex(score: number): string {
  if (score >= 90) return "#4ade80";
  if (score >= 70) return "#fbbf24";
  return "#f87171";
}

export function healthLabel(score: number): string {
  if (score >= 90) return "Excellent";
  if (score >= 80) return "Good";
  if (score >= 70) return "Fair";
  return "Poor";
}

export function tagStyle(tag: string): string {
  const map: Record<string, string> = {
    PK: "bg-blue-500/10 text-blue-400 border-blue-500/25",
    FK: "bg-violet-500/10 text-violet-400 border-violet-500/25",
    PII: "bg-red-500/10 text-red-400 border-red-500/25",
    System: "bg-amber-500/10 text-amber-400 border-amber-500/25",
  };
  return map[tag] || "bg-green-500/10 text-green-400 border-green-500/25";
}
