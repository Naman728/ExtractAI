"use client";

import { DashboardShell } from "@/components/dashboard/shell";
import { useDashboardSession } from "@/components/dashboard/shared";

const MOCK_WEEKLY = [12, 18, 9, 24, 31, 22, 17];

function BarChart({
  data,
  labels,
}: {
  data: number[];
  labels: string[];
}) {
  const max = Math.max(...data, 1);

  return (
    <div className="flex h-48 items-end gap-2 sm:gap-3">
      {data.map((value, i) => (
        <div key={labels[i]} className="flex flex-1 flex-col items-center gap-2">
          <div className="relative flex w-full flex-1 items-end justify-center">
            <div
              className="w-full max-w-[2.5rem] rounded-t-md bg-gradient-to-t from-accent-dim to-accent transition-all dark:from-teal-900 dark:to-accent"
              style={{ height: `${(value / max) * 100}%`, minHeight: value > 0 ? "8px" : "2px" }}
              title={`${labels[i]}: ${value}`}
            />
          </div>
          <span className="text-[10px] font-medium text-slate-500 sm:text-xs dark:text-slate-400">
            {labels[i]}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const { jobs, ready } = useDashboardSession();

  if (!ready) return null;

  const items = jobs?.items ?? [];
  const total = jobs?.total ?? items.length;
  const completed = items.filter((j) => j.status === "completed").length;
  const failed = items.filter((j) => j.status === "failed").length;
  const successRate = total > 0 ? Math.round((completed / total) * 100) : 0;

  const statusCounts = items.reduce<Record<string, number>>((acc, j) => {
    acc[j.status] = (acc[j.status] ?? 0) + 1;
    return acc;
  }, {});

  const dayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  function buildWeeklyVolume(): number[] {
    const days = [0, 0, 0, 0, 0, 0, 0];
    for (const job of items) {
      const d = new Date(job.created_at).getDay();
      const idx = d === 0 ? 6 : d - 1;
      days[idx]++;
    }
    return days.some((v) => v > 0) ? days : MOCK_WEEKLY;
  }

  const chartData = buildWeeklyVolume();

  return (
    <DashboardShell
      title="Analytics"
      description="Extraction volume, success rates, and pipeline health."
    >
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard label="Total volume" value={String(total)} sub="Jobs in workspace" />
        <MetricCard label="Success rate" value={`${successRate}%`} sub={`${completed} completed`} />
        <MetricCard label="Failed" value={String(failed)} sub="Needs attention" accent={failed > 0} />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <Panel title="Weekly volume">
          <BarChart data={chartData} labels={dayLabels} />
          {items.length === 0 ? (
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
              Showing sample data until jobs are recorded.
            </p>
          ) : null}
        </Panel>

        <Panel title="Status breakdown">
          <div className="space-y-4">
            {Object.keys(statusCounts).length > 0 ? (
              Object.entries(statusCounts).map(([status, count]) => (
                <StatusRow key={status} label={status} count={count} total={items.length} />
              ))
            ) : (
              <>
                <StatusRow label="completed" count={0} total={1} />
                <StatusRow label="running" count={0} total={1} />
                <StatusRow label="pending" count={0} total={1} />
              </>
            )}
          </div>
        </Panel>
      </div>

      <Panel title="Strategy usage" className="mt-6">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from(
            items.reduce<Map<string, number>>((m, j) => {
              const s = j.strategy_used ?? "auto";
              m.set(s, (m.get(s) ?? 0) + 1);
              return m;
            }, new Map()),
          ).length > 0 ? (
            Array.from(
              items.reduce<Map<string, number>>((m, j) => {
                const s = j.strategy_used ?? "auto";
                m.set(s, (m.get(s) ?? 0) + 1);
                return m;
              }, new Map()),
            ).map(([strategy, count]) => (
              <div
                key={strategy}
                className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800/50"
              >
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {strategy}
                </p>
                <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{count}</p>
              </div>
            ))
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">No strategy data yet.</p>
          )}
        </div>
      </Panel>
    </DashboardShell>
  );
}

function MetricCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <p className="text-sm text-slate-600 dark:text-slate-400">{label}</p>
      <p
        className={`mt-2 font-display text-3xl font-semibold ${accent ? "text-signal" : "text-slate-900 dark:text-white"}`}
      >
        {value}
      </p>
      <p className="mt-1 text-xs text-slate-500">{sub}</p>
    </div>
  );
}

function Panel({
  title,
  children,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900 ${className}`}
    >
      <h2 className="mb-4 text-sm font-semibold text-slate-900 dark:text-white">{title}</h2>
      {children}
    </div>
  );
}

function StatusRow({ label, count, total }: { label: string; count: number; total: number }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="capitalize text-slate-700 dark:text-slate-300">{label}</span>
        <span className="text-slate-500 dark:text-slate-400">{count}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className="h-full rounded-full bg-accent transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
