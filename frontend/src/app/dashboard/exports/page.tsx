"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard/shell";
import { jobHref, useDashboardSession } from "@/components/dashboard/shared";
import { api } from "@/lib/api";
import { getValidAccessToken } from "@/lib/auth";

type Format = "json" | "csv" | "excel";

export default function ExportsPage() {
  const { jobs, ready, token } = useDashboardSession();
  const [format, setFormat] = useState<Format>("json");
  const [jobId, setJobId] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const completed = useMemo(
    () => (jobs?.items || []).filter((j) => j.status === "completed"),
    [jobs],
  );

  if (!ready) return null;

  async function generate() {
    setMessage(null);
    setError(null);
    const selected = jobId || completed[0]?.id;
    if (!selected) {
      setError("No completed job to export. Run an extraction first.");
      return;
    }
    setBusy(true);
    try {
      const access = (await getValidAccessToken()) || token;
      if (!access) {
        setError("Session expired — sign in again.");
        return;
      }
      await api.downloadExport(selected, format, access);
      setMessage(`${format.toUpperCase()} download started.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <DashboardShell
      title="Exports"
      description="Download structured JSON, CSV, or Excel from your completed extractions."
    >
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Exportable jobs</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">
            {completed.length}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Formats</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">
            JSON · CSV · Excel
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Auth</p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
            Signed-in downloads only
          </p>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-slate-900 dark:text-white">
            Completed jobs
          </h2>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            {completed.length === 0 ? (
              <p className="px-4 py-8 text-sm text-slate-600 dark:text-slate-400">
                No completed jobs yet.{" "}
                <Link href="/" className="font-semibold text-accent hover:underline">
                  Run an extraction
                </Link>
                .
              </p>
            ) : (
              <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
                <thead className="bg-slate-50 dark:bg-slate-800/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Job
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Strategy
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {completed.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3">
                        <p className="max-w-md truncate text-sm font-medium text-slate-900 dark:text-white">
                          {row.url}
                        </p>
                        <p className="text-xs text-slate-500">
                          {new Date(row.created_at).toLocaleString()}
                        </p>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">
                        {row.strategy_used || "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <Link
                            href={jobHref(row)}
                            className="text-sm font-medium text-slate-600 hover:underline dark:text-slate-300"
                          >
                            Results
                          </Link>
                          <button
                            type="button"
                            className="text-sm font-medium text-accent hover:underline"
                            onClick={() => {
                              setJobId(row.id);
                              setFormat("json");
                            }}
                          >
                            Select
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div>
          <h2 className="mb-4 text-sm font-semibold text-slate-900 dark:text-white">New export</h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Job
              <select
                value={jobId || completed[0]?.id || ""}
                onChange={(e) => setJobId(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                {completed.length === 0 ? (
                  <option value="">No completed jobs</option>
                ) : (
                  completed.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.url.slice(0, 60)}
                    </option>
                  ))
                )}
              </select>
            </label>
            <label className="mt-3 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Format
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value as Format)}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="excel">Excel</option>
              </select>
            </label>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
              Downloads use your account. You must own the job.
            </p>
            {error ? <p className="mt-2 text-sm font-medium text-orange-600">{error}</p> : null}
            {message ? <p className="mt-2 text-sm font-medium text-teal-700">{message}</p> : null}
            <button
              type="button"
              disabled={busy || completed.length === 0}
              onClick={() => void generate()}
              className="mt-4 w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-dim disabled:opacity-50"
            >
              {busy ? "Preparing…" : `Download ${format.toUpperCase()}`}
            </button>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
