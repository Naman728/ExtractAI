"use client";

import Link from "next/link";

import { DashboardShell } from "@/components/dashboard/shell";
import { jobHref, statusBadgeClass, useDashboardSession } from "@/components/dashboard/shared";

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <p className="text-sm font-medium text-slate-600 dark:text-slate-400">{label}</p>
      <p className="mt-2 font-display text-3xl font-semibold text-slate-900 dark:text-white">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">{hint}</p> : null}
    </div>
  );
}

function DataPreviewEmpty() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-6 py-12 text-center dark:border-slate-700 dark:bg-slate-900/50">
      <svg viewBox="0 0 120 80" className="mb-4 h-20 w-28 text-slate-300 dark:text-slate-600" aria-hidden>
        <rect x="8" y="12" width="104" height="56" rx="6" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M20 48h24M20 40h40M20 32h32" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <circle cx="88" cy="28" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M82 28l4 4 8-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M8 52h104" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" opacity="0.5" />
      </svg>
      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">No data preview yet</p>
      <p className="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">
        Run an extraction to see structured fields, confidence scores, and export-ready JSON here.
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const { jobs, jobsLoading, jobsError, user, ready } = useDashboardSession();

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-void dark:bg-slate-950">
        <p className="text-sm text-slate-600 dark:text-slate-400">Loading dashboard…</p>
      </div>
    );
  }

  const completed = jobs?.items.filter((j) => j.status === "completed").length ?? 0;
  const running =
    jobs?.items.filter((j) => j.status === "running" || j.status === "pending").length ?? 0;

  return (
    <DashboardShell
      title="Overview"
      description={user ? `Welcome back, ${user.email}` : "Your extraction workspace"}
    >
      <div className="mb-6 flex flex-wrap gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-dim"
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
            <path d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z" />
          </svg>
          New extraction
        </Link>
        <Link
          href="/dashboard/exports"
          className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-600"
        >
          Manage exports
        </Link>
        <Link
          href="/dashboard/analytics"
          className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-600"
        >
          View analytics
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Total jobs" value={jobs ? String(jobs.total) : "—"} hint="All time" />
        <StatCard label="Completed" value={jobs ? String(completed) : "—"} hint="Successful extractions" />
        <StatCard label="Running" value={jobs ? String(running) : "—"} hint="Pending or in progress" />
      </div>

      <section id="recent-jobs" className="mt-10 scroll-mt-24">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Recent jobs</h2>
          <Link href="/dashboard/analytics" className="text-sm text-accent hover:underline">
            Analytics →
          </Link>
        </div>

        {jobsLoading ? (
          <p className="text-sm text-slate-600 dark:text-slate-400">Loading jobs…</p>
        ) : null}
        {jobsError ? (
          <p className="text-sm text-signal">{(jobsError as Error).message}</p>
        ) : null}

        {!jobsLoading && jobs && jobs.items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-white p-8 text-center dark:border-slate-700 dark:bg-slate-900">
            <p className="text-slate-600 dark:text-slate-400">No jobs yet.</p>
            <Link href="/" className="mt-3 inline-block text-sm font-medium text-accent hover:underline">
              Run your first extraction →
            </Link>
          </div>
        ) : null}

        {jobs && jobs.items.length > 0 ? (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card dark:border-slate-800 dark:bg-slate-900">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
                <thead className="bg-slate-50 dark:bg-slate-800/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      URL
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Status
                    </th>
                    <th className="hidden px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 md:table-cell dark:text-slate-400">
                      Strategy
                    </th>
                    <th className="hidden px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 lg:table-cell dark:text-slate-400">
                      Created
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {jobs.items.slice(0, 10).map((job) => (
                    <tr key={job.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="max-w-xs truncate px-4 py-3 font-mono text-sm text-slate-800 dark:text-slate-200">
                        {job.url}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${statusBadgeClass(job.status)}`}
                        >
                          {job.status}
                        </span>
                      </td>
                      <td className="hidden px-4 py-3 text-sm text-slate-600 md:table-cell dark:text-slate-400">
                        {job.strategy_used ?? "—"}
                      </td>
                      <td className="hidden px-4 py-3 text-sm text-slate-600 lg:table-cell dark:text-slate-400">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={jobHref(job)}
                          className="text-sm font-medium text-accent hover:underline"
                        >
                          {job.status === "completed" ? "Results" : job.batch_id ? "Batch" : "Status"}
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </section>

      <section className="mt-10">
        <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">Data preview</h2>
        {jobs && jobs.items.some((j) => j.status === "completed") ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Open a completed job to inspect extracted fields, tables, and export formats.
            </p>
            <Link
              href={jobHref(jobs.items.find((j) => j.status === "completed")!)}
              className="mt-3 inline-block text-sm font-medium text-accent hover:underline"
            >
              View latest results →
            </Link>
          </div>
        ) : (
          <DataPreviewEmpty />
        )}
      </section>
    </DashboardShell>
  );
}
