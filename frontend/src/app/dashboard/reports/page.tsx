"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PipelineRun, BusinessReport } from "@/lib/api";
import { cn, healthColor, healthBarHex } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Download,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Database,
  ArrowRight,
  BookOpen,
  BarChart3,
  Table2,
  Eye,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Sparkles,
  Shield,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/* ── Severity badge ─────────────────────────────────────────── */
function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase",
        severity === "critical"
          ? "bg-red-500/15 text-red-400"
          : "bg-amber-500/15 text-amber-400",
      )}
    >
      {severity === "critical" ? (
        <AlertTriangle className="h-2.5 w-2.5" />
      ) : (
        <AlertCircle className="h-2.5 w-2.5" />
      )}
      {severity}
    </span>
  );
}

/* ── Stat Card ──────────────────────────────────────────────── */
function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
}) {
  const colors: Record<string, string> = {
    blue: "text-blue-400 bg-blue-500/10",
    emerald: "text-emerald-400 bg-emerald-500/10",
    amber: "text-amber-400 bg-amber-500/10",
    violet: "text-violet-400 bg-violet-500/10",
    red: "text-red-400 bg-red-500/10",
    cyan: "text-cyan-400 bg-cyan-500/10",
  };
  return (
    <div className="flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
      <div
        className={cn(
          "flex h-9 w-9 items-center justify-center rounded-lg",
          colors[color] || colors.blue,
        )}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className="text-lg font-bold tabular-nums text-zinc-100">{value}</p>
        <p className="text-[10px] uppercase tracking-wider text-zinc-500">
          {label}
        </p>
      </div>
    </div>
  );
}

/* ── Collapsible Table Section ──────────────────────────────── */
function TableSection({ table }: { table: any }) {
  const [open, setOpen] = useState(false);
  const hs = table.health_score;

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/30">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-zinc-800/40"
      >
        <div className="flex items-center gap-3">
          <Table2 className="h-4 w-4 text-zinc-500" />
          <span className="text-sm font-semibold text-zinc-200">
            {table.table_name}
          </span>
          <span className="text-[10px] text-zinc-600">
            {table.row_count.toLocaleString()} rows · {table.column_count} cols
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${hs}%`,
                  backgroundColor: healthBarHex(hs),
                }}
              />
            </div>
            <span
              className={cn(
                "text-xs font-medium tabular-nums",
                healthColor(hs),
              )}
            >
              {hs}%
            </span>
          </div>
          {open ? (
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          ) : (
            <ChevronRight className="h-4 w-4 text-zinc-500" />
          )}
        </div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="border-t border-zinc-800 p-4">
              {table.description && (
                <p className="mb-3 text-xs text-zinc-400 italic">
                  {table.description}
                </p>
              )}
              {table.foreign_keys?.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-1.5">
                  {table.foreign_keys.map((fk: any, i: number) => (
                    <span
                      key={i}
                      className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] text-blue-400"
                    >
                      {fk.column} → {fk.referred_table}.{fk.referred_column}
                    </span>
                  ))}
                </div>
              )}
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-zinc-800 text-left text-zinc-500">
                      <th className="pb-2 pr-4 font-medium">Column</th>
                      <th className="pb-2 pr-4 font-medium">Type</th>
                      <th className="pb-2 pr-4 font-medium">Null%</th>
                      <th className="pb-2 pr-4 font-medium">Unique%</th>
                      <th className="pb-2 pr-4 font-medium">PII</th>
                      <th className="pb-2 font-medium">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {table.columns?.map((col: any) => (
                      <tr
                        key={col.name}
                        className="border-b border-zinc-800/50 text-zinc-300"
                      >
                        <td className="py-1.5 pr-4 font-mono text-blue-300">
                          {col.name}
                        </td>
                        <td className="py-1.5 pr-4 text-zinc-500">
                          {col.type}
                        </td>
                        <td className="py-1.5 pr-4 tabular-nums">
                          <span
                            className={
                              col.null_percentage > 50
                                ? "text-red-400"
                                : col.null_percentage > 20
                                  ? "text-amber-400"
                                  : "text-zinc-400"
                            }
                          >
                            {col.null_percentage}%
                          </span>
                        </td>
                        <td className="py-1.5 pr-4 tabular-nums text-zinc-400">
                          {col.unique_percentage}%
                        </td>
                        <td className="py-1.5 pr-4">
                          {col.potential_pii && (
                            <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                          )}
                        </td>
                        <td className="py-1.5 text-zinc-400">
                          {col.description || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   MAIN REPORTS PAGE
   ══════════════════════════════════════════════════════════════ */
export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<"preview" | "raw">("preview");

  // Get pipeline runs
  const { data: runs = [] } = useQuery<PipelineRun[]>({
    queryKey: ["runs"],
    queryFn: api.listRuns,
  });

  const latestRun = runs.find((r) => r.status === "completed") || null;

  // Fetch business report
  const {
    data: report,
    isLoading,
    error,
    refetch,
  } = useQuery<BusinessReport>({
    queryKey: ["report", latestRun?.run_id],
    queryFn: () => api.getBusinessReport(latestRun!.run_id),
    enabled: !!latestRun,
    staleTime: 1000 * 60 * 10, // cache 10 min
  });

  const handleDownload = (format: "json" | "markdown") => {
    if (!latestRun) return;
    const url =
      format === "json"
        ? api.getReportJsonUrl(latestRun.run_id)
        : api.getReportMarkdownUrl(latestRun.run_id);
    window.open(url, "_blank");
  };

  const handleDownloadDict = (format: "json" | "markdown") => {
    if (!latestRun) return;
    window.open(api.getExportUrl(latestRun.run_id, format), "_blank");
  };

  // ── No pipeline run ──
  if (!latestRun) {
    return (
      <div className="mx-auto max-w-5xl">
        <h1 className="text-2xl font-bold text-zinc-100">Reports</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Generate business-ready documentation from your schema analysis
        </p>
        <div className="mt-12 flex flex-col items-center justify-center text-zinc-600">
          <Database className="mb-4 h-12 w-12" />
          <p className="text-sm">Run the pipeline first to generate reports.</p>
        </div>
      </div>
    );
  }

  // ── Loading ──
  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl">
        <h1 className="text-2xl font-bold text-zinc-100">Reports</h1>
        <div className="mt-16 flex flex-col items-center justify-center gap-3">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <Sparkles className="h-8 w-8 text-blue-400" />
          </motion.div>
          <p className="text-sm text-zinc-400">
            Generating AI-enhanced business report...
          </p>
          <p className="text-xs text-zinc-600">
            This may take a moment as Gemini analyzes your schema.
          </p>
        </div>
      </div>
    );
  }

  // ── Error ──
  if (error || !report) {
    return (
      <div className="mx-auto max-w-5xl">
        <h1 className="text-2xl font-bold text-zinc-100">Reports</h1>
        <div className="mt-12 flex flex-col items-center justify-center gap-3 text-red-400">
          <AlertTriangle className="h-8 w-8" />
          <p className="text-sm">Failed to generate report.</p>
          <button
            onClick={() => refetch()}
            className="rounded-lg bg-zinc-800 px-4 py-2 text-xs text-zinc-300 hover:bg-zinc-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const stats = report.database_statistics;
  const overview = report.executive_overview;
  const issues = report.quality_issues || [];
  const criticalCount = issues.filter((i) => i.severity === "critical").length;
  const warningCount = issues.filter((i) => i.severity === "warning").length;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Business Report</h1>
          <p className="mt-1 text-sm text-zinc-500">
            AI-enhanced data dictionary & quality assessment — Run{" "}
            <span className="font-mono text-zinc-400">{latestRun.run_id}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleDownloadDict("json")}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-700 px-3 py-2 text-xs text-zinc-300 transition-colors hover:bg-zinc-800"
          >
            <Download className="h-3.5 w-3.5" />
            Dict JSON
          </button>
          <button
            onClick={() => handleDownloadDict("markdown")}
            className="flex items-center gap-1.5 rounded-lg border border-zinc-700 px-3 py-2 text-xs text-zinc-300 transition-colors hover:bg-zinc-800"
          >
            <Download className="h-3.5 w-3.5" />
            Dict MD
          </button>
          <button
            onClick={() => handleDownload("markdown")}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-blue-500"
          >
            <FileText className="h-3.5 w-3.5" />
            Full Report MD
          </button>
          <button
            onClick={() => handleDownload("json")}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-emerald-500"
          >
            <Download className="h-3.5 w-3.5" />
            Full Report JSON
          </button>
        </div>
      </div>

      {/* Executive Overview */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6"
      >
        <div className="mb-4 flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-blue-400" />
          <h2 className="text-sm font-semibold text-zinc-200">
            Executive Overview
          </h2>
          <span className="rounded-full bg-violet-500/15 px-2 py-0.5 text-[10px] font-bold text-violet-400">
            {overview.business_domain}
          </span>
        </div>
        <p className="mb-4 text-sm leading-relaxed text-zinc-300">
          {overview.executive_summary}
        </p>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {/* Key Findings */}
          <div>
            <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-zinc-400">
              <TrendingUp className="h-3.5 w-3.5 text-cyan-400" />
              Key Findings
            </h3>
            <ul className="space-y-1.5">
              {overview.key_findings.map((f, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-start gap-2 text-xs text-zinc-300"
                >
                  <ArrowRight className="mt-0.5 h-3 w-3 flex-shrink-0 text-cyan-400" />
                  {f}
                </motion.li>
              ))}
            </ul>
          </div>

          {/* Recommendations */}
          <div>
            <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-zinc-400">
              <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
              Recommendations
            </h3>
            <ul className="space-y-1.5">
              {overview.recommendations.map((r, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-start gap-2 text-xs text-zinc-300"
                >
                  <CheckCircle2 className="mt-0.5 h-3 w-3 flex-shrink-0 text-emerald-400" />
                  {r}
                </motion.li>
              ))}
            </ul>
          </div>
        </div>

        {/* Data Governance */}
        {overview.data_governance_notes && (
          <div className="mt-4 rounded-lg bg-amber-500/5 border border-amber-500/20 p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <Shield className="h-3.5 w-3.5 text-amber-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">
                Data Governance
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              {overview.data_governance_notes}
            </p>
          </div>
        )}

        <div className="mt-4 rounded-lg bg-zinc-800/50 p-3">
          <p className="text-xs font-medium text-zinc-300">
            <span className="text-emerald-400">Overall Assessment:</span>{" "}
            {overview.overall_assessment}
          </p>
        </div>
      </motion.div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard
          label="Tables"
          value={stats.total_tables}
          icon={Table2}
          color="blue"
        />
        <StatCard
          label="Columns"
          value={stats.total_columns}
          icon={BarChart3}
          color="violet"
        />
        <StatCard
          label="Rows"
          value={stats.total_rows.toLocaleString()}
          icon={Database}
          color="cyan"
        />
        <StatCard
          label="Health"
          value={`${stats.average_health_score}%`}
          icon={CheckCircle2}
          color="emerald"
        />
        <StatCard
          label="PII Cols"
          value={stats.pii_columns_detected}
          icon={ShieldAlert}
          color={stats.pii_columns_detected > 0 ? "amber" : "emerald"}
        />
        <StatCard
          label="FK Links"
          value={stats.foreign_key_count}
          icon={ExternalLink}
          color="blue"
        />
      </div>

      {/* Quality Issues */}
      {issues.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5"
        >
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
              <h2 className="text-sm font-semibold text-zinc-200">
                Data Quality Issues
              </h2>
            </div>
            <div className="flex gap-2">
              {criticalCount > 0 && (
                <span className="rounded-full bg-red-500/15 px-2 py-0.5 text-[10px] font-bold text-red-400">
                  {criticalCount} Critical
                </span>
              )}
              {warningCount > 0 && (
                <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-bold text-amber-400">
                  {warningCount} Warnings
                </span>
              )}
            </div>
          </div>
          <div className="space-y-2">
            {issues.map((issue, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-start gap-3 rounded-lg border border-zinc-800/50 bg-zinc-900/30 p-3"
              >
                <SeverityBadge severity={issue.severity} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-zinc-300">
                    <span className="font-mono text-blue-300">
                      {issue.table}
                    </span>{" "}
                    — {issue.issue}
                  </p>
                  <p className="mt-0.5 text-[11px] text-zinc-500">
                    {issue.recommendation}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Relationships */}
      {report.relationships.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5"
        >
          <div className="mb-4 flex items-center gap-2">
            <ExternalLink className="h-5 w-5 text-blue-400" />
            <h2 className="text-sm font-semibold text-zinc-200">
              Table Relationships
            </h2>
            <span className="text-xs text-zinc-600">
              ({report.relationships.length} foreign keys)
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-zinc-800 text-left text-zinc-500">
                  <th className="pb-2 pr-6 font-medium">Source Table</th>
                  <th className="pb-2 pr-6 font-medium">Column</th>
                  <th className="pb-2 pr-6 font-medium"></th>
                  <th className="pb-2 pr-6 font-medium">Target Table</th>
                  <th className="pb-2 font-medium">Column</th>
                </tr>
              </thead>
              <tbody>
                {report.relationships.map((rel, i) => (
                  <tr
                    key={i}
                    className="border-b border-zinc-800/30 text-zinc-300"
                  >
                    <td className="py-1.5 pr-6 font-mono text-cyan-300">
                      {rel.source_table}
                    </td>
                    <td className="py-1.5 pr-6 font-mono text-zinc-400">
                      {rel.source_column}
                    </td>
                    <td className="py-1.5 pr-6 text-zinc-600">→</td>
                    <td className="py-1.5 pr-6 font-mono text-emerald-300">
                      {rel.target_table}
                    </td>
                    <td className="py-1.5 font-mono text-zinc-400">
                      {rel.target_column}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Table Documentation */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="mb-3 flex items-center gap-2">
          <Database className="h-5 w-5 text-violet-400" />
          <h2 className="text-sm font-semibold text-zinc-200">
            Table Documentation
          </h2>
          <span className="text-xs text-zinc-600">
            ({report.tables.length} tables)
          </span>
        </div>
        <div className="space-y-2">
          {report.tables.map((table) => (
            <TableSection key={table.table_name} table={table} />
          ))}
        </div>
      </motion.div>
    </div>
  );
}
