"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

import { PipelineOrchestra, type PipelineEvent } from "@/components/pipeline-orchestra";
import { SiteHeader } from "@/components/site-header";
import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import { getGuestKey } from "@/lib/guest";

type Job = {
  id: string;
  url: string;
  status: string;
  progress_pct: number;
  current_stage: string | null;
  error_code: string | null;
  error_message: string | null;
  pipeline_version: string;
  strategy_used: string | null;
};

type JobEvents = {
  job_id: string;
  status: string;
  progress_pct: number;
  current_stage: string | null;
  events: PipelineEvent[];
};

export default function JobStatusPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const jobId = params.id;

  const { data, error, isLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () =>
      api.get<Job>(`/api/v1/jobs/${jobId}`, getGuestKey(), getAccessToken()),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status === "pending" || status === "running" ? 1200 : false;
    },
  });

  const { data: eventsData } = useQuery({
    queryKey: ["job-events", jobId],
    queryFn: () =>
      api.get<JobEvents>(
        `/api/v1/jobs/${jobId}/events`,
        getGuestKey(),
        getAccessToken(),
      ),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status === "pending" || status === "running" ? 1000 : false;
    },
  });

  useEffect(() => {
    if (data?.status === "completed") {
      const t = setTimeout(() => router.replace(`/results/${jobId}`), 600);
      return () => clearTimeout(t);
    }
  }, [data?.status, jobId, router]);

  return (
    <main className="min-h-screen bg-void">
      <SiteHeader />
      <div className="mx-auto max-w-5xl px-5 pb-16 pt-2 md:px-6">
        <Link href="/" className="text-sm text-accent hover:underline">
          ← Home
        </Link>
        <div className="mt-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-display text-3xl text-slate-900 md:text-4xl">
              {data?.status === "completed" ? "Extraction complete" : "Running extraction"}
            </h1>
            <p className="mt-2 text-sm text-slate-700">
              {data?.status === "completed"
                ? "Orchestra stopped — opening results…"
                : "Live pipeline graph — each node is a real stage in the ExtractAI engine."}
            </p>
          </div>
          {data?.status === "completed" ? (
            <Link
              href={`/results/${jobId}`}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-dim"
            >
              View results →
            </Link>
          ) : null}
        </div>

        {isLoading ? (
          <div className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
            <div className="border-b border-slate-200 px-5 py-4">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-accent">
                Extraction orchestra
              </p>
              <p className="mt-1 text-sm font-medium text-slate-700">Connecting to job worker…</p>
            </div>
            <div className="orchestra-canvas flex h-48 items-center justify-center">
              <div className="orchestra-node is-active rounded-xl px-6 py-4">
                <p className="orch-label">Initializing pipeline</p>
                <p className="orch-sub mt-1">Wiring intelligence → extract → AI</p>
              </div>
            </div>
          </div>
        ) : null}
        {error ? <p className="mt-8 text-signal">{(error as Error).message}</p> : null}

        {data && data.status !== "completed" ? (
          <div className="mt-8">
            <PipelineOrchestra job={data} events={eventsData?.events ?? []} />
          </div>
        ) : null}

        {data?.status === "completed" ? (
          <div className="mt-8 rounded-2xl border border-teal-200 bg-teal-50 px-5 py-8 text-center">
            <p className="font-display text-2xl text-slate-900">Results ready</p>
            <p className="mt-2 text-sm font-medium text-slate-700">
              Redirecting to the results page…
            </p>
            <Link
              href={`/results/${jobId}`}
              className="mt-5 inline-flex rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent-dim"
            >
              Open results now
            </Link>
          </div>
        ) : null}
      </div>
    </main>
  );
}
