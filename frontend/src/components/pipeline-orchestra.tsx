"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

import { OrchestraViewport } from "@/components/orchestra-viewport";

export type OrchestraJob = {
  url: string;
  status: string;
  progress_pct: number;
  current_stage: string | null;
  strategy_used: string | null;
  error_code: string | null;
  error_message: string | null;
};

export type PipelineEvent = {
  stage: string;
  level: string;
  message: string;
  created_at: string;
};

type NodeDef = {
  id: string;
  label: string;
  subtitle: string;
  x: number;
  y: number;
  stages: string[];
};

const NODES: NodeDef[] = [
  { id: "start", label: "URL", subtitle: "Input", x: 40, y: 160, stages: ["pending"] },
  {
    id: "intelligence",
    label: "Intelligence",
    subtitle: "Profile site",
    x: 200,
    y: 80,
    stages: ["intelligence", "running"],
  },
  {
    id: "strategy",
    label: "Strategy",
    subtitle: "Pick engine",
    x: 200,
    y: 240,
    stages: ["strategy"],
  },
  {
    id: "network",
    label: "Network",
    subtitle: "Discover APIs",
    x: 380,
    y: 40,
    stages: ["network"],
  },
  {
    id: "fetch",
    label: "Fetch",
    subtitle: "Browser / HTTP",
    x: 380,
    y: 160,
    stages: ["fetch", "browser_agent"],
  },
  {
    id: "extract",
    label: "Extract",
    subtitle: "Plugins",
    x: 380,
    y: 280,
    stages: ["plugins", "clean", "extract"],
  },
  {
    id: "normalize",
    label: "Normalize",
    subtitle: "Schema",
    x: 560,
    y: 120,
    stages: ["normalize", "validate", "persist"],
  },
  {
    id: "ai",
    label: "AI Understand",
    subtitle: "Knowledge",
    x: 560,
    y: 260,
    stages: ["understanding"],
  },
  {
    id: "done",
    label: "Results",
    subtitle: "Structured JSON",
    x: 740,
    y: 160,
    stages: ["completed"],
  },
];

const EDGES: [string, string][] = [
  ["start", "intelligence"],
  ["start", "strategy"],
  ["intelligence", "network"],
  ["intelligence", "fetch"],
  ["strategy", "fetch"],
  ["strategy", "extract"],
  ["network", "normalize"],
  ["fetch", "extract"],
  ["extract", "normalize"],
  ["extract", "ai"],
  ["normalize", "done"],
  ["ai", "done"],
];

const STAGE_ORDER = [
  "pending",
  "running",
  "intelligence",
  "strategy",
  "network",
  "fetch",
  "clean",
  "plugins",
  "normalize",
  "validate",
  "persist",
  "understanding",
  "completed",
];

function stageIndex(stage: string | null | undefined): number {
  if (!stage) return 0;
  const i = STAGE_ORDER.indexOf(stage.toLowerCase());
  return i >= 0 ? i : 1;
}

function nodeState(
  node: NodeDef,
  currentStage: string | null,
  status: string,
): "pending" | "active" | "done" | "failed" {
  if (status === "failed") {
    const cur = stageIndex(currentStage);
    const mine = Math.min(...node.stages.map((s) => stageIndex(s)));
    if (mine <= cur) return node.stages.some((s) => s === (currentStage || "").toLowerCase()) ? "failed" : "done";
    return "pending";
  }
  if (status === "completed") return "done";

  const cur = stageIndex(currentStage || (status === "pending" ? "pending" : "running"));
  const nodeStages = node.stages.map((s) => stageIndex(s));
  const min = Math.min(...nodeStages);
  const max = Math.max(...nodeStages);

  if (cur > max) return "done";
  if (cur >= min && cur <= max) return "active";
  // progress-based fallback for sparse stage updates
  return "pending";
}

function nodeByProgress(progress: number, status: string): string {
  if (status === "completed") return "done";
  if (progress < 8) return "start";
  if (progress < 20) return "intelligence";
  if (progress < 35) return "strategy";
  if (progress < 50) return "network";
  if (progress < 65) return "fetch";
  if (progress < 78) return "extract";
  if (progress < 88) return "normalize";
  if (progress < 98) return "ai";
  return "done";
}

const ACTIVITY: Record<string, string[]> = {
  start: ["Queued extraction job", "Validating public URL"],
  intelligence: ["Probing headers & HTML", "Detecting framework / CMS", "Reading robots & metadata"],
  strategy: ["Scoring extraction strategies", "Selecting fetch engine"],
  network: ["Scanning for JSON endpoints", "Classifying XHR / GraphQL hints"],
  fetch: ["Fetching page content", "Preserving session cookies", "Waiting for DOM settle"],
  extract: ["Running extraction plugins", "Collecting emails, links, products", "Cleaning HTML"],
  normalize: ["Mapping to schema", "Validating field quality"],
  ai: ["Building website summary", "Extracting entities", "Assembling knowledge graph"],
  done: ["Structured payload ready", "Redirecting to results"],
  failed: ["Pipeline halted", "Inspect error details below"],
};

function fmtTime(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleTimeString();
}

export function PipelineOrchestra({
  job,
  events = [],
}: {
  job: OrchestraJob;
  events?: PipelineEvent[];
}) {
  const [tick, setTick] = useState(0);
  const [fallbackLog, setFallbackLog] = useState<string[]>([]);

  const live = job.status === "pending" || job.status === "running";
  const hasRealEvents = events.length > 0;

  // Prefer the real stage reported by the latest backend event.
  const latestStage = hasRealEvents
    ? events[events.length - 1].stage
    : job.current_stage;

  const activeId = useMemo(() => {
    if (job.status === "failed") return "failed";
    if (job.status === "completed") return "done";
    const byStage = NODES.find((n) =>
      n.stages.includes((latestStage || "").toLowerCase()),
    )?.id;
    return byStage || nodeByProgress(job.progress_pct, job.status);
  }, [latestStage, job.progress_pct, job.status]);

  // Real activity feed straight from the backend pipeline logs (newest first).
  const realLog = useMemo(() => {
    return events
      .slice(-9)
      .reverse()
      .map((e) => `${fmtTime(e.created_at)}  ${e.message}`);
  }, [events]);

  useEffect(() => {
    if (!live || hasRealEvents) return;
    const t = setInterval(() => setTick((x) => x + 1), 1600);
    return () => clearInterval(t);
  }, [live, hasRealEvents]);

  useEffect(() => {
    if (hasRealEvents) return; // real feed drives the log
    if (!live) {
      const finalLine =
        job.status === "completed"
          ? `${new Date().toLocaleTimeString()}  Structured payload ready`
          : `${new Date().toLocaleTimeString()}  Pipeline halted`;
      setFallbackLog((prev) => (prev[0]?.includes("ready") || prev[0]?.includes("halted") ? prev : [finalLine, ...prev].slice(0, 8)));
      return;
    }
    const key = job.status === "failed" ? "failed" : activeId;
    const lines = ACTIVITY[key] || ACTIVITY.fetch;
    const line = lines[tick % lines.length];
    setFallbackLog((prev) => {
      const next = [`${new Date().toLocaleTimeString()}  ${line}`, ...prev];
      return next.slice(0, 8);
    });
  }, [activeId, tick, job.status, live, hasRealEvents]);

  const log = hasRealEvents ? realLog : fallbackLog;
  const stageLabel = latestStage ?? "queued";

  const nodeMap = Object.fromEntries(NODES.map((n) => [n.id, n]));

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent">Extraction orchestra</p>
          <p className="mt-1 break-all font-mono text-xs font-medium text-slate-700">{job.url}</p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="rounded-full bg-accent-soft px-3 py-1 font-semibold text-accent-dim">
            {job.status}
          </span>
          <span className="font-mono font-semibold text-slate-800">{job.progress_pct}%</span>
          {!live ? (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
              Orchestra stopped
            </span>
          ) : null}
        </div>
      </div>

      <OrchestraViewport contentWidth={860} contentHeight={360} hint={live ? "Drag to pan · scroll to explore" : "Complete · opening results"}>
        <svg
          width={860}
          height={360}
          viewBox="0 0 860 360"
          className="block"
          role="img"
          aria-label="Extraction pipeline graph"
          style={{ width: 860, height: 360 }}
        >
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill="#94a3b8" />
            </marker>
          </defs>

          {EDGES.map(([from, to]) => {
            const a = nodeMap[from];
            const b = nodeMap[to];
            const x1 = a.x + 70;
            const y1 = a.y + 28;
            const x2 = b.x;
            const y2 = b.y + 28;
            const mx = (x1 + x2) / 2;
            const path = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
            const aState = nodeState(a, latestStage, job.status);
            const flowing =
              live &&
              (aState === "done" || aState === "active") &&
              (activeId === to || nodeState(b, latestStage, job.status) !== "pending");
            return (
              <path
                key={`${from}-${to}`}
                d={path}
                fill="none"
                stroke={job.status === "completed" || flowing ? "#0d9488" : "#cbd5e1"}
                strokeWidth={flowing ? 2.2 : 1.5}
                markerEnd="url(#arrow)"
                className={flowing ? "orchestra-edge-flow" : undefined}
                opacity={flowing || job.status === "completed" ? 1 : 0.7}
              />
            );
          })}

          {NODES.map((n) => {
            let state = nodeState(n, latestStage, job.status);
            // Progress-based activation when backend stages are sparse
            if (live && state === "pending" && activeId === n.id) state = "active";
            if (job.status === "completed") state = "done";
            if (live && job.progress_pct > 0 && state === "pending") {
              const order = NODES.map((x) => x.id);
              if (order.indexOf(n.id) < order.indexOf(activeId === "failed" ? "start" : activeId)) {
                state = "done";
              }
            }

            return (
              <g key={n.id} transform={`translate(${n.x}, ${n.y})`}>
                <foreignObject width="140" height="64">
                  <div
                    className={`orchestra-node flex h-[56px] flex-col justify-center rounded-xl px-3 ${
                      live && state === "active" ? "is-active" : ""
                    } ${state === "done" ? "is-done" : ""} ${state === "failed" ? "is-failed" : ""}`}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          state === "active"
                            ? `bg-accent ${live ? "orchestra-pulse" : ""}`
                            : state === "done"
                              ? "bg-teal-500"
                              : state === "failed"
                                ? "bg-orange-500"
                                : "bg-slate-400"
                        }`}
                      />
                      <p className="orch-label">{n.label}</p>
                    </div>
                    <p className="orch-sub mt-0.5 pl-4">{n.subtitle}</p>
                  </div>
                </foreignObject>
              </g>
            );
          })}
        </svg>
      </OrchestraViewport>

      <div className="grid gap-0 border-t border-slate-200 md:grid-cols-[1.2fr_0.8fr]">
        <div className="border-b border-slate-200 px-5 py-4 md:border-b-0 md:border-r">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-800">
            Live activity
          </p>
          <ul className="mt-3 space-y-1.5 font-mono text-xs font-semibold text-slate-900">
            <AnimatePresence initial={false}>
              {log.map((line, idx) => (
                <motion.li
                  key={`${idx}-${line}`}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="truncate text-slate-900"
                >
                  {line}
                </motion.li>
              ))}
            </AnimatePresence>
          </ul>
        </div>
        <div className="px-5 py-4">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-700">
            Pipeline
          </p>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="font-medium text-slate-700">Stage</dt>
              <dd className="font-semibold text-slate-900">{stageLabel}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-700">Strategy</dt>
              <dd className="font-semibold text-slate-900">{job.strategy_used ?? "deciding…"}</dd>
            </div>
          </dl>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-accent to-accent-blue"
              animate={{ width: `${Math.max(job.progress_pct, job.status === "pending" ? 4 : 8)}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
          {job.status === "failed" && job.error_message ? (
            <p className="mt-4 rounded-lg border border-orange-200 bg-orange-50 p-3 text-sm text-orange-700">
              {job.error_code}: {job.error_message}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
