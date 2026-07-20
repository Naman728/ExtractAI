"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { BatchOrchestra, BatchOrchestraSkeleton } from "@/components/batch-orchestra";
import { SiteHeader } from "@/components/site-header";
import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import { getGuestKey } from "@/lib/guest";

type BatchItem = {
  id: string;
  position: number;
  address: string;
  job_id: string | null;
  status: string;
  error_message: string | null;
  officials_total: number;
  officials_counts: Record<string, number>;
};

type Batch = {
  id: string;
  url: string;
  workflow: string | null;
  status: string;
  total_items: number;
  completed_items: number;
  failed_items: number;
  progress_pct: number;
  items: BatchItem[];
};

type BatchResults = {
  batch_id: string;
  status: string;
  results: Array<{
    address: string;
    status: string;
    job_id: string | null;
    error_message: string | null;
    officials: {
      federal?: Array<{ name: string; office: string }>;
      state?: Array<{ name: string; office: string }>;
      local?: Array<{ name: string; office: string }>;
      total?: number;
      counts?: Record<string, number>;
    };
  }>;
};

export default function BatchPage() {
  const params = useParams<{ id: string }>();
  const batchId = params.id;
  const resultsRef = useRef<HTMLDivElement>(null);
  const [showOrchestra, setShowOrchestra] = useState(true);

  const { data, error, isLoading } = useQuery({
    queryKey: ["batch", batchId],
    queryFn: () =>
      api.get<Batch>(`/api/v1/batches/${batchId}`, getGuestKey(), getAccessToken()),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status === "pending" || status === "running" ? 1500 : false;
    },
  });

  const done =
    data &&
    (data.status === "completed" || data.status === "partial" || data.status === "failed");

  const { data: results } = useQuery({
    queryKey: ["batch-results", batchId],
    queryFn: () =>
      api.get<BatchResults>(
        `/api/v1/batches/${batchId}/results`,
        getGuestKey(),
        getAccessToken(),
      ),
    enabled: Boolean(done),
  });

  // When batch finishes: hide orchestra immediately so results sit at the top.
  useEffect(() => {
    if (!done) {
      setShowOrchestra(true);
      return;
    }
    setShowOrchestra(false);
    const scrollT = setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 150);
    return () => clearTimeout(scrollT);
  }, [done, data?.status]);

  return (
    <main className="min-h-screen bg-void">
      <SiteHeader />
      <div className="mx-auto max-w-6xl px-5 pb-16 pt-2 md:px-6">
        <Link href="/" className="text-sm text-accent hover:underline">
          ← Home
        </Link>
        <div className="mt-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-display text-3xl text-slate-900 md:text-4xl">
              {done ? "Batch results" : "Batch extraction"}
            </h1>
            <p className="mt-2 text-sm font-medium text-slate-700">
              {done
                ? "Extraction finished — orchestra stopped. Review officials below."
                : "Fan-out orchestra — each address is a live worker node pulling from the site."}
            </p>
          </div>
          {data ? (
            <dl className="flex flex-wrap gap-4 text-sm">
              <div>
                <dt className="font-medium text-slate-700">Completed</dt>
                <dd className="font-semibold text-slate-900">{data.completed_items}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-700">Failed</dt>
                <dd className="font-semibold text-slate-900">{data.failed_items}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-700">Progress</dt>
                <dd className="font-semibold text-slate-900">{data.progress_pct}%</dd>
              </div>
            </dl>
          ) : null}
        </div>

        {error ? <p className="mt-6 font-medium text-signal">{(error as Error).message}</p> : null}

        {done ? (
          <div className="mt-6 flex flex-wrap items-center gap-3 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-900">
            <span className="font-semibold">
              Batch {data?.status} — {data?.completed_items}/{data?.total_items} workers finished.
            </span>
            {!showOrchestra ? (
              <button
                type="button"
                className="rounded-lg border border-teal-300 bg-white px-3 py-1 text-xs font-semibold text-teal-800 hover:bg-teal-50"
                onClick={() => setShowOrchestra(true)}
              >
                Show final orchestra
              </button>
            ) : (
              <button
                type="button"
                className="rounded-lg border border-teal-300 bg-white px-3 py-1 text-xs font-semibold text-teal-800 hover:bg-teal-50"
                onClick={() => {
                  setShowOrchestra(false);
                  resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
              >
                Hide orchestra · view results
              </button>
            )}
            <a
              href="#batch-results"
              className="ml-auto text-xs font-semibold text-accent hover:underline"
            >
              Jump to results ↓
            </a>
          </div>
        ) : null}

        {showOrchestra || !done ? (
          <div className="mt-8">
            {isLoading || !data ? <BatchOrchestraSkeleton /> : <BatchOrchestra batch={data} />}
          </div>
        ) : null}

        <div ref={resultsRef} id="batch-results" className="scroll-mt-8">
          {results?.results?.length ? (
            <div className="mt-10 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-display text-2xl text-slate-900">Officials by address</h2>
                <button
                  type="button"
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-950"
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(results, null, 2))}
                >
                  Copy JSON
                </button>
              </div>
              {results.results.map((r) => (
                <div
                  key={r.address}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-slate-900">{r.address}</p>
                      <p className="mt-1 text-xs font-medium text-slate-700">
                        {r.status}
                        {r.officials?.total != null ? ` · ${r.officials.total} total` : ""}
                      </p>
                    </div>
                    {r.job_id && r.status === "completed" ? (
                      <Link
                        href={`/results/${r.job_id}`}
                        className="text-xs font-semibold text-accent hover:underline"
                      >
                        Full results →
                      </Link>
                    ) : null}
                  </div>
                  {r.status === "completed" ? (
                    <div className="mt-3 grid gap-3 md:grid-cols-3">
                      {(["federal", "state", "local"] as const).map((level) => (
                        <div key={level}>
                          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
                            {level}
                          </p>
                          <ul className="space-y-1 text-sm text-slate-800">
                            {(r.officials?.[level] || []).map((o) => (
                              <li key={`${o.name}-${o.office}`}>
                                <span className="font-medium text-slate-900">{o.name}</span>
                                <span className="block text-xs font-medium text-slate-700">
                                  {o.office}
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  ) : r.error_message ? (
                    <p className="mt-3 text-sm text-orange-700">{r.error_message}</p>
                  ) : null}
                </div>
              ))}
            </div>
          ) : done ? (
            <p className="mt-10 text-sm font-medium text-slate-700">Loading batch results…</p>
          ) : null}
        </div>
      </div>
    </main>
  );
}
