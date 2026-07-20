"use client";

import { useState } from "react";

import { DashboardShell } from "@/components/dashboard/shell";
import { ComingSoonBanner } from "@/components/dashboard/coming-soon-banner";
import { useDashboardSession } from "@/components/dashboard/shared";

type ExportRow = {
  id: string;
  name: string;
  format: string;
  size: string;
  created: string;
  status: "ready" | "processing" | "failed";
};

const MOCK_EXPORTS: ExportRow[] = [
  {
    id: "exp_1",
    name: "Q1 product catalog",
    format: "JSON",
    size: "2.4 MB",
    created: "2026-07-18",
    status: "ready",
  },
  {
    id: "exp_2",
    name: "Pricing snapshot",
    format: "CSV",
    size: "840 KB",
    created: "2026-07-17",
    status: "ready",
  },
  {
    id: "exp_3",
    name: "Full site crawl",
    format: "NDJSON",
    size: "—",
    created: "2026-07-16",
    status: "processing",
  },
];

export default function ExportsPage() {
  const { jobs, ready } = useDashboardSession();
  const [exports] = useState(MOCK_EXPORTS);
  const [format, setFormat] = useState("json");

  if (!ready) return null;

  const completedJobs = jobs?.items.filter((j) => j.status === "completed").length ?? 0;

  return (
    <DashboardShell
      title="Exports"
      description="Download and manage structured output from completed extractions."
    >
      <ComingSoonBanner
        feature="Exports history"
        detail="This list is mock data. Real exports still work from each job’s Results page (JSON / CSV / Excel via the API)."
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Exportable jobs</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{completedJobs}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Saved exports</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{exports.length}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-400">Formats</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">JSON · CSV · NDJSON</p>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-slate-900 dark:text-white">Export history</h2>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
              <thead className="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                    Format
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 sm:table-cell dark:text-slate-400">
                    Size
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {exports.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium text-slate-900 dark:text-white">{row.name}</p>
                      <p className="text-xs text-slate-500">{row.created}</p>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">{row.format}</td>
                    <td className="hidden px-4 py-3 text-sm text-slate-600 sm:table-cell dark:text-slate-400">
                      {row.size}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {row.status === "ready" ? (
                        <button
                          type="button"
                          className="text-sm font-medium text-accent hover:underline"
                        >
                          Download
                        </button>
                      ) : (
                        <span className="text-xs capitalize text-slate-500">{row.status}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h2 className="mb-4 text-sm font-semibold text-slate-900 dark:text-white">New export</h2>
          <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Format
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="ndjson">NDJSON</option>
              </select>
            </label>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
              Export completed jobs from the results page, or bulk-export from a batch view.
            </p>
            <button
              type="button"
              className="mt-4 w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-dim"
            >
              Generate {format.toUpperCase()} export
            </button>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
