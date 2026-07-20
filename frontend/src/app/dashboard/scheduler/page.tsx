"use client";

import { useState } from "react";

import { DashboardShell } from "@/components/dashboard/shell";
import { ComingSoonBanner } from "@/components/dashboard/coming-soon-banner";
import { useDashboardSession } from "@/components/dashboard/shared";

type ScheduledJob = {
  id: string;
  name: string;
  url: string;
  cron: string;
  nextRun: string;
  enabled: boolean;
};

const MOCK_SCHEDULES: ScheduledJob[] = [
  {
    id: "sch_1",
    name: "Product catalog sync",
    url: "https://example.com/products",
    cron: "0 */6 * * *",
    nextRun: "Today, 6:00 PM",
    enabled: true,
  },
  {
    id: "sch_2",
    name: "Pricing monitor",
    url: "https://example.com/pricing",
    cron: "0 9 * * 1-5",
    nextRun: "Tomorrow, 9:00 AM",
    enabled: false,
  },
];

export default function SchedulerPage() {
  const { ready } = useDashboardSession();
  const [schedules] = useState(MOCK_SCHEDULES);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [cron, setCron] = useState("0 */6 * * *");

  if (!ready) return null;

  return (
    <DashboardShell
      title="Scheduler"
      description="Automate recurring extractions on a cron schedule."
    >
      <ComingSoonBanner
        feature="Job scheduler"
        detail="Schedules shown here are a UI preview. Cron execution is not wired to the backend yet — run jobs manually from the home page or API."
      />

      <div className="grid gap-8 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <h2 className="mb-4 text-sm font-semibold text-slate-900 dark:text-white">
            Active schedules
          </h2>
          <div className="space-y-3">
            {schedules.map((sch) => (
              <div
                key={sch.id}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">{sch.name}</p>
                    <p className="mt-1 truncate font-mono text-xs text-slate-500 dark:text-slate-400">
                      {sch.url}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      sch.enabled
                        ? "bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-300"
                        : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                    }`}
                  >
                    {sch.enabled ? "Enabled" : "Paused"}
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500 dark:text-slate-400">
                  <span>Cron: {sch.cron}</span>
                  <span>Next: {sch.nextRun}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-slate-900 dark:text-white">
            Create schedule
          </h2>
          <form
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900"
            onSubmit={(e) => {
              e.preventDefault();
            }}
          >
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                placeholder="Weekly competitor scrape"
              />
            </label>
            <label className="mt-4 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Target URL
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                placeholder="https://"
              />
            </label>
            <label className="mt-4 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Cron expression
              <input
                value={cron}
                onChange={(e) => setCron(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </label>
            <button
              type="submit"
              disabled
              className="mt-5 w-full rounded-lg bg-accent/50 px-4 py-2.5 text-sm font-semibold text-white cursor-not-allowed"
            >
              Save schedule (coming soon)
            </button>
          </form>
        </div>
      </div>
    </DashboardShell>
  );
}
