"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PipelineRun } from "@/lib/api";
import { cn, healthColor, healthBgColor, healthLabel } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import {
  Table2,
  Search,
  ChevronDown,
  ChevronRight,
  Key,
  Link2,
  Hash,
  Type,
  Calendar,
  Binary,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
} from "lucide-react";
import { toast } from "sonner";

// ── Column Type Icon ────────────────────────────────────────────
function TypeIcon({ type }: { type: string }) {
  const t = type.toLowerCase();
  if (
    t.includes("int") ||
    t.includes("decimal") ||
    t.includes("float") ||
    t.includes("numeric")
  )
    return <Hash className="h-3.5 w-3.5 text-violet-400" />;
  if (t.includes("char") || t.includes("text") || t.includes("string"))
    return <Type className="h-3.5 w-3.5 text-blue-400" />;
  if (t.includes("date") || t.includes("time"))
    return <Calendar className="h-3.5 w-3.5 text-amber-400" />;
  if (t.includes("bool") || t.includes("bit"))
    return <Binary className="h-3.5 w-3.5 text-emerald-400" />;
  return <Type className="h-3.5 w-3.5 text-zinc-500" />;
}

// ── Column Row ──────────────────────────────────────────────────
function ColumnRow({ col }: { col: any }) {
  const [copied, setCopied] = useState(false);

  const copyName = () => {
    navigator.clipboard.writeText(col.name);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="group flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-zinc-800/50">
      {/* Type Icon */}
      <TypeIcon type={col.type || ""} />

      {/* Name + Meta */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-zinc-200">{col.name}</span>
          {col.is_primary_key && (
            <span className="flex items-center gap-0.5 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-400">
              <Key className="h-2.5 w-2.5" /> PK
            </span>
          )}
          {col.is_foreign_key && (
            <span className="flex items-center gap-0.5 rounded bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-medium text-blue-400">
              <Link2 className="h-2.5 w-2.5" /> FK
            </span>
          )}
        </div>
        {col.ai_description && (
          <p className="mt-0.5 text-xs text-zinc-500 line-clamp-2">
            {col.ai_description}
          </p>
        )}
      </div>

      {/* Data Type */}
      <span className="rounded-md bg-zinc-800 px-2 py-0.5 font-mono text-[11px] text-zinc-400">
        {col.type || "unknown"}
      </span>

      {/* Nullable */}
      <span
        className={cn(
          "text-[10px] font-medium",
          col.nullable ? "text-zinc-600" : "text-zinc-400",
        )}
      >
        {col.nullable ? "NULL" : "NOT NULL"}
      </span>

      {/* Copy button */}
      <button
        onClick={copyName}
        className="opacity-0 transition-opacity group-hover:opacity-100"
      >
        {copied ? (
          <Check className="h-3.5 w-3.5 text-emerald-400" />
        ) : (
          <Copy className="h-3.5 w-3.5 text-zinc-600 hover:text-zinc-400" />
        )}
      </button>
    </div>
  );
}

// ── Table Card ──────────────────────────────────────────────────
function TableCard({
  name,
  table,
  isExpanded,
  onToggle,
}: {
  name: string;
  table: any;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const score = table.quality_score ?? table.health_score ?? 0;
  // Normalize columns: backend returns dict {name: {...}}, convert to array
  const columnsRaw = table.columns || {};
  const columns: any[] = Array.isArray(columnsRaw)
    ? columnsRaw
    : Object.entries(columnsRaw).map(([colName, colData]: [string, any]) => ({
        name: colData.name || colName,
        type: colData.original_type || colData.type || "",
        is_primary_key: colData.is_primary_key ?? false,
        is_foreign_key: colData.is_foreign_key ?? false,
        nullable: colData.nullable ?? true,
        ai_description: colData.description || colData.ai_description || null,
        ...colData,
      }));

  return (
    <motion.div
      layout
      className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50"
    >
      {/* Header */}
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-5 py-4 text-left transition-colors hover:bg-zinc-800/30"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          ) : (
            <ChevronRight className="h-4 w-4 text-zinc-500" />
          )}
          <Table2 className="h-4 w-4 text-blue-400" />
          <span className="font-mono text-sm font-medium text-zinc-100">
            {name}
          </span>
          <span className="text-xs text-zinc-600">
            {columns.length} columns
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Health Badge */}
          <div
            className={cn(
              "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
              healthBgColor(score),
              healthColor(score),
            )}
          >
            {score >= 80 ? (
              <CheckCircle2 className="h-3 w-3" />
            ) : score >= 50 ? (
              <ShieldCheck className="h-3 w-3" />
            ) : (
              <AlertTriangle className="h-3 w-3" />
            )}
            {score}% {healthLabel(score)}
          </div>
        </div>
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {/* AI Description */}
            {table.ai_description && (
              <div className="mx-5 mb-3 rounded-lg bg-blue-500/5 border border-blue-500/10 px-4 py-3">
                <p className="text-xs text-blue-300/80">
                  {table.ai_description}
                </p>
              </div>
            )}

            {/* Column Header */}
            <div className="flex items-center gap-3 border-t border-zinc-800 px-5 py-2 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
              <span className="w-5" />
              <span className="flex-1">Column</span>
              <span className="w-24 text-center">Type</span>
              <span className="w-16 text-center">Nullable</span>
              <span className="w-6" />
            </div>

            {/* Columns */}
            <div className="border-t border-zinc-800/50 px-2 pb-3">
              {columns.map((col: any) => (
                <ColumnRow key={col.name} col={col} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Schema Explorer Page ────────────────────────────────────────
export default function SchemaPage() {
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");

  const { data: runs = [] } = useQuery<PipelineRun[]>({
    queryKey: ["runs"],
    queryFn: api.listRuns,
  });

  const latestRun = runs.length > 0 ? runs[0] : null;
  const schema = latestRun?.result || {};

  const toggleTable = (name: string) => {
    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const expandAll = () => setExpandedTables(new Set(Object.keys(schema)));
  const collapseAll = () => setExpandedTables(new Set());

  // Filter tables
  const filteredTables = Object.entries(schema).filter(
    ([name, table]: [string, any]) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      if (name.toLowerCase().includes(q)) return true;
      const colsArray = Array.isArray(table.columns)
        ? table.columns
        : Object.entries(table.columns || {}).map(([k, v]: [string, any]) => ({
            name: v.name || k,
            ...v,
          }));
      return colsArray.some((col: any) =>
        (col.name || "").toLowerCase().includes(q),
      );
    },
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Schema Explorer</h1>
          <p className="mt-1 text-sm text-zinc-500">
            {filteredTables.length} tables documented
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={expandAll}
            className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          type="text"
          placeholder="Search tables and columns..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-xl border border-zinc-800 bg-zinc-900/50 py-2.5 pl-10 pr-4 text-sm text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-blue-500/50"
        />
      </div>

      {/* Table Cards */}
      <div className="space-y-3">
        {filteredTables.length > 0 ? (
          filteredTables.map(([name, table]) => (
            <TableCard
              key={name}
              name={name}
              table={table}
              isExpanded={expandedTables.has(name)}
              onToggle={() => toggleTable(name)}
            />
          ))
        ) : latestRun ? (
          <div className="flex flex-col items-center py-16 text-zinc-600">
            <Search className="mb-3 h-8 w-8" />
            <p className="text-sm">No tables match your search.</p>
          </div>
        ) : (
          <div className="flex flex-col items-center py-16 text-zinc-600">
            <Table2 className="mb-3 h-10 w-10" />
            <p className="text-sm">
              Run the pipeline from the Dashboard to generate documentation.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
