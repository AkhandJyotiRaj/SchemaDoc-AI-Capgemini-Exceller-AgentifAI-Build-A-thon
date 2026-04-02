"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { PipelineLogEntry } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  Database,
  Brain,
  ShieldCheck,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Zap,
  AlertTriangle,
  ChevronDown,
  ArrowDown,
} from "lucide-react";
import { useState } from "react";

/* ── Stage metadata ─────────────────────────────────────────── */
const STAGE_META: Record<
  string,
  {
    label: string;
    icon: React.ElementType;
    color: string;
    glow: string;
    bg: string;
    border: string;
  }
> = {
  extract: {
    label: "Schema Extraction",
    icon: Database,
    color: "text-cyan-400",
    glow: "shadow-cyan-500/20",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
  },
  enrich: {
    label: "AI Enrichment",
    icon: Brain,
    color: "text-violet-400",
    glow: "shadow-violet-500/20",
    bg: "bg-violet-500/10",
    border: "border-violet-500/30",
  },
  validate: {
    label: "Integrity Validation",
    icon: ShieldCheck,
    color: "text-emerald-400",
    glow: "shadow-emerald-500/20",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
  },
};

/* ── Animated connector line between stages ─────────────────── */
function Connector({ active, failed }: { active: boolean; failed?: boolean }) {
  return (
    <div className="relative flex h-8 items-center justify-center">
      {/* Vertical line */}
      <motion.div
        className={cn(
          "w-0.5 h-full rounded-full",
          failed
            ? "bg-red-500/40"
            : active
              ? "bg-gradient-to-b from-blue-500/60 to-blue-500/20"
              : "bg-zinc-800",
        )}
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
        transition={{ duration: 0.4 }}
      />
      {/* Pulse traveling down */}
      {active && !failed && (
        <motion.div
          className="absolute w-1.5 h-1.5 rounded-full bg-blue-400"
          initial={{ top: 0, opacity: 1 }}
          animate={{ top: "100%", opacity: 0 }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            ease: "easeIn",
          }}
        />
      )}
    </div>
  );
}

/* ── Retry loop arrow ───────────────────────────────────────── */
function RetryArrow({ attempt }: { attempt: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.5, x: 20 }}
      animate={{ opacity: 1, scale: 1, x: 0 }}
      className="relative my-1 flex items-center justify-center"
    >
      <div className="flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1">
        <motion.div
          animate={{ rotate: -360 }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <RotateCcw className="h-3 w-3 text-amber-400" />
        </motion.div>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">
          Retry #{attempt}
        </span>
        <motion.div
          className="h-1.5 w-1.5 rounded-full bg-amber-400"
          animate={{ opacity: [1, 0.3, 1] }}
          transition={{ duration: 0.8, repeat: Infinity }}
        />
      </div>
    </motion.div>
  );
}

/* ── Single pipeline stage card ─────────────────────────────── */
function StageCard({
  entry,
  index,
  isRetry,
}: {
  entry: PipelineLogEntry;
  index: number;
  isRetry: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const meta = STAGE_META[entry.step] || STAGE_META.extract;
  const Icon = meta.icon;
  const isFailed = entry.status === "failed";
  const isPassed = entry.status === "passed" || entry.status === "success";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.15, duration: 0.4, ease: "easeOut" }}
    >
      <div
        className={cn(
          "group relative overflow-hidden rounded-xl border transition-all duration-300",
          isFailed
            ? "border-red-500/40 bg-red-500/5"
            : isPassed
              ? cn("border-zinc-700/50", meta.bg)
              : "border-zinc-800 bg-zinc-900/50",
          isFailed && "shadow-lg shadow-red-500/10",
          isPassed &&
            entry.step === "validate" &&
            "shadow-lg shadow-emerald-500/10",
        )}
      >
        {/* Success shimmer for validate pass */}
        {isPassed && entry.step === "validate" && (
          <motion.div
            className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-emerald-400/5 to-transparent"
            initial={{ x: "-100%" }}
            animate={{ x: "200%" }}
            transition={{
              duration: 2,
              repeat: Infinity,
              repeatDelay: 3,
              ease: "easeInOut",
            }}
          />
        )}

        {/* Failure pulse for validate fail */}
        {isFailed && (
          <motion.div
            className="pointer-events-none absolute inset-0 rounded-xl border-2 border-red-500/30"
            animate={{ opacity: [0, 0.6, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}

        <div className="relative p-3">
          {/* Header */}
          <div className="flex items-center gap-3">
            {/* Animated icon container */}
            <div className={cn("relative flex-shrink-0")}>
              <motion.div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-lg",
                  isFailed ? "bg-red-500/15" : cn(meta.bg),
                )}
                animate={
                  isFailed
                    ? { scale: [1, 1.05, 1] }
                    : isPassed && entry.step === "validate"
                      ? { scale: [1, 1.08, 1] }
                      : {}
                }
                transition={{ duration: 2, repeat: Infinity }}
              >
                {isFailed ? (
                  <XCircle className="h-4.5 w-4.5 text-red-400" />
                ) : isPassed && entry.step === "validate" ? (
                  <motion.div
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{
                      type: "spring",
                      stiffness: 200,
                      damping: 12,
                    }}
                  >
                    <CheckCircle2 className="h-4.5 w-4.5 text-emerald-400" />
                  </motion.div>
                ) : (
                  <Icon className={cn("h-4.5 w-4.5", meta.color)} />
                )}
              </motion.div>

              {/* Live activity ring */}
              {isPassed && !isFailed && (
                <motion.div
                  className={cn(
                    "absolute -inset-0.5 rounded-lg border",
                    entry.step === "validate"
                      ? "border-emerald-500/40"
                      : meta.border,
                  )}
                  initial={{ opacity: 0, scale: 1.1 }}
                  animate={{ opacity: [0, 0.6, 0], scale: [1, 1.15, 1.2] }}
                  transition={{ duration: 2, delay: index * 0.15 }}
                />
              )}
            </div>

            {/* Title & message */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "text-xs font-semibold uppercase tracking-wider",
                    isFailed ? "text-red-400" : meta.color,
                  )}
                >
                  {meta.label}
                </span>
                {isRetry && (
                  <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[9px] font-bold uppercase text-amber-400">
                    Retry
                  </span>
                )}
                {isPassed && (
                  <motion.span
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[9px] font-bold uppercase text-emerald-400"
                  >
                    {entry.step === "validate" ? "Verified" : "Done"}
                  </motion.span>
                )}
                {isFailed && (
                  <motion.span
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="rounded bg-red-500/15 px-1.5 py-0.5 text-[9px] font-bold uppercase text-red-400"
                  >
                    Failed
                  </motion.span>
                )}
              </div>
              <p className="mt-0.5 truncate text-[11px] text-zinc-400">
                {entry.message}
              </p>
            </div>

            {/* Expand button for errors */}
            {isFailed && entry.errors.length > 0 && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="rounded-lg p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
              >
                <motion.div
                  animate={{ rotate: expanded ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ChevronDown className="h-4 w-4" />
                </motion.div>
              </button>
            )}
          </div>

          {/* Error details (expandable) */}
          <AnimatePresence>
            {expanded && entry.errors.length > 0 && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="mt-2 space-y-1 rounded-lg bg-red-500/5 p-2">
                  {entry.errors.map((err, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-start gap-1.5 text-[10px] text-red-300/80"
                    >
                      <AlertTriangle className="mt-0.5 h-2.5 w-2.5 flex-shrink-0 text-red-400" />
                      <span>{err}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

/* ── Particle Burst (on validate pass) ──────────────────────── */
function ParticleBurst() {
  const particles = Array.from({ length: 8 }, (_, i) => ({
    id: i,
    angle: (i / 8) * 360,
  }));

  return (
    <div className="pointer-events-none absolute inset-0 flex items-center justify-center overflow-hidden">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute h-1 w-1 rounded-full bg-emerald-400"
          initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
          animate={{
            x: Math.cos((p.angle * Math.PI) / 180) * 40,
            y: Math.sin((p.angle * Math.PI) / 180) * 40,
            opacity: 0,
            scale: 0,
          }}
          transition={{
            duration: 0.8,
            delay: 0.1,
            ease: "easeOut",
          }}
        />
      ))}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   MAIN COMPONENT — PipelineVisualizer
   ══════════════════════════════════════════════════════════════ */
export default function PipelineVisualizer({
  log,
}: {
  log: PipelineLogEntry[];
}) {
  if (!log || log.length === 0) return null;

  // Determine retry attempts for enrichment passes
  let enrichCount = 0;
  const enrichedLog = log.map((entry) => {
    if (entry.step === "enrich") {
      enrichCount++;
      return { ...entry, _enrichPass: enrichCount, _isRetry: enrichCount > 1 };
    }
    return { ...entry, _enrichPass: 0, _isRetry: false };
  });

  const lastEntry = enrichedLog[enrichedLog.length - 1];
  const pipelinePassed =
    lastEntry?.step === "validate" && lastEntry?.status === "passed";
  const totalRetries = enrichCount > 1 ? enrichCount - 1 : 0;

  return (
    <div className="relative space-y-0">
      {/* Pipeline status header */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <motion.div
            className={cn(
              "h-2 w-2 rounded-full",
              pipelinePassed ? "bg-emerald-400" : "bg-blue-400",
            )}
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <span className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
            Pipeline Trace
          </span>
        </div>
        {totalRetries > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2 py-0.5"
          >
            <Zap className="h-2.5 w-2.5 text-amber-400" />
            <span className="text-[9px] font-bold text-amber-400">
              {totalRetries} {totalRetries === 1 ? "retry" : "retries"}
            </span>
          </motion.div>
        )}
      </div>

      {/* Pipeline stages */}
      {enrichedLog.map((entry, i) => {
        const prev = i > 0 ? enrichedLog[i - 1] : null;
        const showRetryArrow =
          prev?.step === "validate" &&
          prev?.status === "failed" &&
          entry.step === "enrich";

        return (
          <div key={`${entry.step}-${i}`}>
            {/* Connector from previous stage */}
            {i > 0 && !showRetryArrow && (
              <Connector
                active={true}
                failed={prev?.step === "validate" && prev?.status === "failed"}
              />
            )}

            {/* Retry arrow when validation failed and we loop back to enrich */}
            {showRetryArrow && (
              <RetryArrow attempt={(entry as any)._enrichPass - 1} />
            )}

            {/* Stage card */}
            <StageCard
              entry={entry}
              index={i}
              isRetry={(entry as any)._isRetry}
            />

            {/* Particle burst on final validate pass */}
            {entry.step === "validate" &&
              entry.status === "passed" &&
              i === enrichedLog.length - 1 && (
                <div className="relative">
                  <ParticleBurst />
                </div>
              )}
          </div>
        );
      })}

      {/* Final result badge */}
      {pipelinePassed && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-3 flex items-center justify-center"
        >
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-4 py-1.5">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 0.5, delay: 0.7 }}
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
            </motion.div>
            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-400">
              Zero Hallucinations · Zero Data Loss
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
}
