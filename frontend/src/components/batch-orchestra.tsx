"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

import { OrchestraViewport } from "@/components/orchestra-viewport";

export type BatchOrchestraItem = {
  id: string;
  position: number;
  address: string;
  job_id: string | null;
  status: string;
  error_message: string | null;
  officials_total: number;
};

export type BatchOrchestraData = {
  id: string;
  url: string;
  workflow: string | null;
  status: string;
  total_items: number;
  completed_items: number;
  failed_items: number;
  progress_pct: number;
  items: BatchOrchestraItem[];
};

const STAGE_LABELS = [
  "Open site",
  "Apply inputs",
  "Navigate results",
  "Parse officials",
  "Normalize",
  "Persist",
];

function statusTone(status: string): "pending" | "active" | "done" | "failed" {
  const s = status.toLowerCase();
  if (s === "completed") return "done";
  if (s === "failed") return "failed";
  if (s === "running") return "active";
  return "pending";
}

function shortAddress(addr: string, max = 42): string {
  if (addr.length <= max) return addr;
  return `${addr.slice(0, max - 1)}…`;
}

/** Skeleton tree shown while batch metadata is still loading. */
export function BatchOrchestraSkeleton() {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
      <div className="border-b border-slate-200 px-5 py-4">
        <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent">
          Batch orchestra
        </p>
        <p className="mt-1 text-sm font-medium text-slate-700">Wiring workers and fanning out jobs…</p>
      </div>
      <div className="orchestra-canvas px-4 py-10">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-8">
          <div className="orchestra-node is-active w-64 rounded-xl px-4 py-3 text-center">
            <p className="orch-label">Batch root</p>
            <p className="orch-sub mt-1 font-mono">initializing</p>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="orchestra-node h-14 w-40 animate-pulse rounded-xl bg-slate-50"
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function BatchOrchestra({ batch }: { batch: BatchOrchestraData }) {
  const [tick, setTick] = useState(0);
  const [log, setLog] = useState<string[]>([]);
  const items = useMemo(
    () => [...batch.items].sort((a, b) => a.position - b.position),
    [batch.items],
  );

  const terminal =
    batch.status === "completed" ||
    batch.status === "partial" ||
    batch.status === "failed";
  const live = !terminal;

  const runningCount = items.filter((i) => i.status === "running").length;
  const pendingCount = items.filter((i) => i.status === "pending").length;

  useEffect(() => {
    if (!live) return;
    const t = setInterval(() => setTick((x) => x + 1), 1400);
    return () => clearInterval(t);
  }, [live]);

  useEffect(() => {
    if (!live) {
      setLog((prev) => {
        const doneLine = `${new Date().toLocaleTimeString()}  Batch ${batch.status} · ${batch.completed_items}/${batch.total_items} done`;
        if (prev[0]?.includes("done")) return prev;
        return [doneLine, ...prev].slice(0, 10);
      });
      return;
    }
    const active = items.find((i) => i.status === "running") || items.find((i) => i.status === "pending");
    const stage = STAGE_LABELS[tick % STAGE_LABELS.length];
    const line = active
      ? `${new Date().toLocaleTimeString()}  ${shortAddress(active.address, 36)} → ${stage}`
      : `${new Date().toLocaleTimeString()}  Batch ${batch.status} · ${batch.completed_items}/${batch.total_items} done`;
    setLog((prev) => [line, ...prev].slice(0, 10));
  }, [tick, items, batch.status, batch.completed_items, batch.total_items, live]);

  // Full tree width for ALL workers (never cap at 4 — that clipped nodes #5+)
  const nodeW = 168;
  const nodeH = 72;
  const gapX = 28;
  const padX = 48;
  const rootW = 300;
  const rootH = 64;
  const rootY = 28;
  const childY = 188;
  const n = Math.max(items.length, 1);
  const totalChildrenW = n * nodeW + Math.max(0, n - 1) * gapX;
  const canvasW = Math.max(rootW + padX * 2, totalChildrenW + padX * 2, 720);
  const canvasH = childY + nodeH + 56;
  const rootX = canvasW / 2 - rootW / 2;
  const startX = Math.max(padX, (canvasW - totalChildrenW) / 2);

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent">
            Batch orchestra
          </p>
          <p className="mt-1 break-all font-mono text-xs font-medium text-slate-700">{batch.url}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="rounded-full bg-accent-soft px-3 py-1 font-semibold text-accent-dim">
            {batch.status}
          </span>
          <span className="font-mono font-semibold text-slate-800">
            {batch.completed_items + batch.failed_items}/{batch.total_items}
          </span>
          {live && runningCount > 0 ? (
            <span className="rounded-full bg-sky-100 px-2.5 py-1 text-xs font-semibold text-sky-800">
              {runningCount} pulling
            </span>
          ) : null}
          {live && pendingCount > 0 ? (
            <span className="rounded-full bg-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-800">
              {pendingCount} queued
            </span>
          ) : null}
          {!live ? (
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
              Orchestra stopped
            </span>
          ) : null}
        </div>
      </div>

      <OrchestraViewport
        contentWidth={canvasW}
        contentHeight={canvasH}
        hint={live ? "Drag to pan · scroll for full tree" : "Complete · drag to review tree"}
      >
        <svg
          width={canvasW}
          height={canvasH}
          viewBox={`0 0 ${canvasW} ${canvasH}`}
          className="block"
          role="img"
          aria-label="Batch extraction tree"
          style={{ width: canvasW, height: canvasH }}
        >
          <defs>
            <marker id="batchArrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill="#64748b" />
            </marker>
          </defs>

          {items.map((item, i) => {
            const cx = startX + i * (nodeW + gapX) + nodeW / 2;
            const x1 = rootX + rootW / 2;
            const y1 = rootY + rootH - 8;
            const x2 = cx;
            const y2 = childY;
            const midY = (y1 + y2) / 2;
            const path = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
            const tone = statusTone(item.status);
            return (
              <path
                key={`edge-${item.id}`}
                d={path}
                fill="none"
                stroke={
                  tone === "failed"
                    ? "#ea580c"
                    : tone === "done"
                      ? "#0d9488"
                      : tone === "active"
                        ? "#0284c7"
                        : "#94a3b8"
                }
                strokeWidth={tone === "active" && live ? 2.4 : 1.6}
                markerEnd="url(#batchArrow)"
                className={live && tone === "active" ? "orchestra-edge-flow" : undefined}
                opacity={tone === "pending" ? 0.55 : 1}
              />
            );
          })}

          <foreignObject x={rootX} y={rootY} width={rootW} height={rootH}>
            <div
              className={`orchestra-node flex h-full flex-col justify-center rounded-xl px-4 ${
                live ? "is-active" : "is-done"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full bg-accent ${live ? "orchestra-pulse" : ""}`}
                />
                <p className="orch-label">Batch fan-out</p>
              </div>
              <p className="orch-sub mt-0.5 truncate pl-5 font-mono">
                {batch.workflow || "browser_agent"} · {batch.total_items} workers
                {!live ? " · finished" : ""}
              </p>
            </div>
          </foreignObject>

          {items.map((item, i) => {
            const x = startX + i * (nodeW + gapX);
            const tone = statusTone(item.status);
            return (
              <foreignObject key={item.id} x={x} y={childY} width={nodeW} height={nodeH}>
                <div
                  className={`orchestra-node flex h-full flex-col justify-center rounded-xl px-3 ${
                    live && tone === "active" ? "is-active" : ""
                  } ${tone === "done" ? "is-done" : ""} ${tone === "failed" ? "is-failed" : ""}`}
                >
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                        tone === "active"
                          ? `bg-sky-500 ${live ? "orchestra-pulse" : ""}`
                          : tone === "done"
                            ? "bg-teal-500"
                            : tone === "failed"
                              ? "bg-orange-500"
                              : "bg-slate-400"
                      }`}
                    />
                    <p className="orch-label truncate" title={item.address}>
                      #{item.position + 1}
                    </p>
                    <span className="orch-meta ml-auto">{item.status}</span>
                  </div>
                  <p className="orch-sub mt-1 line-clamp-2" title={item.address}>
                    {item.address}
                  </p>
                </div>
              </foreignObject>
            );
          })}
        </svg>
      </OrchestraViewport>

      <div className="grid gap-0 border-t border-slate-200 lg:grid-cols-[1fr_1.1fr]">
        <div className="border-b border-slate-200 px-5 py-4 lg:border-b-0 lg:border-r">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-800">
            {live ? "Live pull log" : "Pull log"}
          </p>
          <ul className="mt-3 max-h-48 space-y-1.5 overflow-auto font-mono text-xs font-semibold text-slate-900">
            <AnimatePresence initial={false}>
              {log.map((line, idx) => (
                <motion.li
                  key={`${idx}-${line}`}
                  initial={live ? { opacity: 0, x: -6 } : false}
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
          <div className="mb-3 flex items-center justify-between">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-800">
              Worker nodes
            </p>
            <div className="h-2 w-32 overflow-hidden rounded-full bg-slate-200">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-accent to-accent-blue"
                animate={{
                  width: `${Math.max(
                    batch.progress_pct,
                    terminal ? 100 : 4,
                  )}%`,
                }}
              />
            </div>
          </div>
          <div className="max-h-56 space-y-2 overflow-auto">
            {items.map((item) => {
              const tone = statusTone(item.status);
              return (
                <div
                  key={item.id}
                  className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm shadow-sm"
                >
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-slate-900">{item.address}</p>
                    <p className="mt-0.5 text-xs font-semibold text-slate-800">
                      <span
                        className={
                          tone === "active"
                            ? "text-sky-800"
                            : tone === "done"
                              ? "text-teal-800"
                              : tone === "failed"
                                ? "text-orange-800"
                                : "text-slate-800"
                        }
                      >
                        {item.status}
                      </span>
                      {item.officials_total ? ` · ${item.officials_total} officials` : ""}
                      {item.error_message ? ` · ${item.error_message}` : ""}
                    </p>
                    {live && tone === "active" ? (
                      <p className="mt-1 font-mono text-[10px] font-semibold text-sky-800">
                        {STAGE_LABELS[tick % STAGE_LABELS.length]}…
                      </p>
                    ) : null}
                  </div>
                  {item.job_id && item.status === "completed" ? (
                    <Link
                      href={`/results/${item.job_id}`}
                      className="shrink-0 text-xs font-semibold text-accent hover:underline"
                    >
                      Results
                    </Link>
                  ) : live && tone === "active" ? (
                    <span className="orchestra-pulse shrink-0 font-mono text-[10px] font-semibold uppercase text-sky-800">
                      live
                    </span>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
