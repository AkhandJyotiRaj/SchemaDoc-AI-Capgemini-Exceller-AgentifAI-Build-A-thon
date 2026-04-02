"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { PipelineRun } from "@/lib/api";
import {
  cn,
  formatNumber,
  healthColor,
  healthLabel,
  healthBarHex,
} from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Database,
  Table2,
  ShieldCheck,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  ChevronRight,
  BarChart3,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import PipelineVisualizer from "@/components/PipelineVisualizer";

// ── Metric Card ──────────────────────────────────────────────────
function MetricCard({
  label,
  value,
  icon: Icon,
  color = "blue",
  delay = 0,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color?: string;
  delay?: number;
}) {
  const colorMap: Record<string, string> = {
    blue: "text-blue-400 bg-blue-500/10",
    emerald: "text-emerald-400 bg-emerald-500/10",
    amber: "text-amber-400 bg-amber-500/10",
    violet: "text-violet-400 bg-violet-500/10",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className="flex items-center gap-4 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
    >
      <div
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-lg",
          colorMap[color],
        )}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold tabular-nums text-zinc-100">{value}</p>
        <p className="text-xs text-zinc-500">{label}</p>
      </div>
    </motion.div>
  );
}

// ── Pipeline Run Button ──────────────────────────────────────────
function PipelineRunner() {
  const queryClient = useQueryClient();
  const [selectedDb, setSelectedDb] = useState("");
  const [customConn, setCustomConn] = useState("");
  const [showCustom, setShowCustom] = useState(false);

  const { data: databases = [] } = useQuery({
    queryKey: ["databases"],
    queryFn: api.listDatabases,
  });

  const mutation = useMutation({
    mutationFn: api.runPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["runs"] });
    },
    onError: (err: Error) => {
      toast.error(err.message || "Pipeline run failed. Please try again.");
    },
  });

  const connString = showCustom ? customConn.trim() : selectedDb;

  return (
    <div className="flex items-center gap-2">
      {!showCustom ? (
        <>
          <select
            value={selectedDb}
            onChange={(e) => setSelectedDb(e.target.value)}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 outline-none focus:border-blue-500"
          >
            <option value="">Select database...</option>
            {databases.map((db: any) => (
              <option key={db.value} value={db.value}>
                {db.label}
              </option>
            ))}
          </select>
          <button
            onClick={() => setShowCustom(true)}
            className="rounded-lg border border-zinc-700 px-2.5 py-2 text-xs text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
            title="Connect to external database"
          >
            🔗 Custom
          </button>
        </>
      ) : (
        <>
          <input
            type="text"
            value={customConn}
            onChange={(e) => setCustomConn(e.target.value)}
            placeholder="snowflake://user:pass@account/db/schema?warehouse=WH"
            className="w-72 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs font-mono text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-blue-500"
          />
          <button
            onClick={() => {
              setShowCustom(false);
              setCustomConn("");
            }}
            className="rounded-lg border border-zinc-700 px-2.5 py-2 text-xs text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
          >
            ← Presets
          </button>
        </>
      )}

      <button
        onClick={() => connString && mutation.mutate({ db_path: connString })}
        disabled={!connString || mutation.isPending}
        className={cn(
          "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all",
          connString && !mutation.isPending
            ? "bg-blue-600 text-white hover:bg-blue-500 active:scale-[0.98]"
            : "cursor-not-allowed bg-zinc-800 text-zinc-500",
        )}
      >
        {mutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Play className="h-4 w-4" />
        )}
        {mutation.isPending ? "Running..." : "Run Pipeline"}
      </button>
    </div>
  );
}

// ── Table Health Row ─────────────────────────────────────────────
function TableHealthRow({
  name,
  score,
  columns,
}: {
  name: string;
  score: number;
  columns: number;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg px-3 py-2 transition-colors hover:bg-zinc-800/50">
      <div className="flex items-center gap-3">
        <Table2 className="h-4 w-4 text-zinc-500" />
        <span className="text-sm text-zinc-200">{name}</span>
        <span className="text-xs text-zinc-600">{columns} cols</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="h-1.5 w-20 overflow-hidden rounded-full bg-zinc-800">
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${score}%`, backgroundColor: healthBarHex(score) }}
          />
        </div>
        <span
          className={cn("text-xs font-medium tabular-nums", healthColor(score))}
        >
          {score}%
        </span>
      </div>
    </div>
  );
}

// ── Main Dashboard ──────────────────────────────────────────────
export default function DashboardPage() {
  const { data: runs = [] } = useQuery<PipelineRun[]>({
    queryKey: ["runs"],
    queryFn: api.listRuns,
    refetchInterval: 5000,
  });

  const latestRun = runs.length > 0 ? runs[0] : null;

  const totalTables = latestRun?.result
    ? Object.keys(latestRun.result).length
    : 0;

  const totalColumns = latestRun?.result
    ? Object.values(latestRun.result).reduce(
        (acc: number, table: any) =>
          acc +
          (Array.isArray(table.columns)
            ? table.columns.length
            : Object.keys(table.columns || {}).length),
        0,
      )
    : 0;

  const avgHealth = latestRun?.result
    ? Math.round(
        Object.values(latestRun.result).reduce(
          (acc: number, table: any) =>
            acc + (table.quality_score ?? table.health_score ?? 0),
          0,
        ) / Math.max(totalTables, 1),
      )
    : 0;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Dashboard</h1>
          <p className="mt-1 text-sm text-zinc-500">
            AI-Powered Data Dictionary Generator
          </p>
        </div>
        <PipelineRunner />
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Tables Documented"
          value={totalTables}
          icon={Table2}
          color="blue"
          delay={0}
        />
        <MetricCard
          label="Columns Analyzed"
          value={formatNumber(totalColumns)}
          icon={BarChart3}
          color="violet"
          delay={0.05}
        />
        <MetricCard
          label="Average Health"
          value={`${avgHealth}%`}
          icon={ShieldCheck}
          color="emerald"
          delay={0.1}
        />
        <MetricCard
          label="Pipeline Runs"
          value={runs.length}
          icon={Clock}
          color="amber"
          delay={0.15}
        />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Table Health List (2/3) */}
        <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-200">
              Table Health
            </h2>
            {latestRun && (
              <Link
                href="/dashboard/schema"
                className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
              >
                View All <ChevronRight className="h-3 w-3" />
              </Link>
            )}
          </div>

          {latestRun?.result ? (
            <div className="space-y-1">
              {Object.entries(latestRun.result)
                .sort(
                  ([, a]: any, [, b]: any) =>
                    (a.quality_score ?? a.health_score ?? 0) -
                    (b.quality_score ?? b.health_score ?? 0),
                )
                .map(([name, table]: [string, any]) => (
                  <TableHealthRow
                    key={name}
                    name={name}
                    score={table.quality_score ?? table.health_score ?? 0}
                    columns={
                      Array.isArray(table.columns)
                        ? table.columns.length
                        : Object.keys(table.columns || {}).length
                    }
                  />
                ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-zinc-600">
              <Database className="mb-3 h-10 w-10" />
              <p className="text-sm">
                No documentation yet. Run the pipeline to get started.
              </p>
            </div>
          )}
        </div>

        {/* Pipeline Log (1/3) */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="mb-4 text-sm font-semibold text-zinc-200">
            Pipeline Activity
          </h2>

          {latestRun?.pipeline_log && latestRun.pipeline_log.length > 0 ? (
            <PipelineVisualizer log={latestRun.pipeline_log} />
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-zinc-600">
              <Sparkles className="mb-3 h-8 w-8" />
              <p className="text-xs">Waiting for pipeline run...</p>
            </div>
          )}

          {/* Recent Runs */}
          {runs.length > 1 && (
            <div className="mt-6 border-t border-zinc-800 pt-4">
              <h3 className="mb-2 text-xs font-medium text-zinc-500">
                Recent Runs
              </h3>
              <div className="space-y-2">
                {runs.slice(0, 5).map((run: PipelineRun) => (
                  <div
                    key={run.run_id}
                    className="flex items-center justify-between rounded-md px-2 py-1.5 text-xs hover:bg-zinc-800/50"
                  >
                    <div className="flex items-center gap-2">
                      {run.status === "completed" ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      ) : run.status === "failed" ? (
                        <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
                      ) : (
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-400" />
                      )}
                      <span className="text-zinc-400 font-mono">
                        {run.run_id.slice(0, 8)}
                      </span>
                    </div>
                    <span className="text-zinc-600">
                      {run.result
                        ? `${Object.keys(run.result).length} tables`
                        : run.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
