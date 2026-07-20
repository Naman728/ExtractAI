"use client";

import { DashboardShell } from "@/components/dashboard/shell";
import { ComingSoonBanner } from "@/components/dashboard/coming-soon-banner";
import { useDashboardSession } from "@/components/dashboard/shared";

type Notification = {
  id: string;
  title: string;
  body: string;
  time: string;
  read: boolean;
  type: "success" | "error" | "info";
};

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: "1",
    title: "Extraction completed",
    body: "Your job for example.com finished with 42 fields extracted.",
    time: "2 hours ago",
    read: false,
    type: "success",
  },
  {
    id: "2",
    title: "Batch progress",
    body: "Batch #8821 is 75% complete (15/20 URLs).",
    time: "5 hours ago",
    read: false,
    type: "info",
  },
  {
    id: "3",
    title: "Job failed",
    body: "Timeout while fetching protected resource on shop.example.com.",
    time: "Yesterday",
    read: true,
    type: "error",
  },
  {
    id: "4",
    title: "Welcome to ExtractAI",
    body: "Run your first extraction from the home page to get started.",
    time: "Jul 12, 2026",
    read: true,
    type: "info",
  },
];

export default function NotificationsPage() {
  const { jobs, ready } = useDashboardSession();

  if (!ready) return null;

  const recentCompleted = jobs?.items.find((j) => j.status === "completed");
  const dynamicNote = recentCompleted
    ? `Latest completed job: ${recentCompleted.url}`
    : null;

  return (
    <DashboardShell title="Notifications" description="Activity from your workspace and extractions.">
      <ComingSoonBanner
        feature="Notification center"
        detail="Most entries below are sample UI. Live job status still appears on the job Orchestra and Results pages."
      />
      {dynamicNote ? (
        <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">{dynamicNote}</p>
      ) : null}

      <div className="mb-4 flex justify-end">
        <button
          type="button"
          className="text-sm font-medium text-accent hover:underline"
        >
          Mark all as read
        </button>
      </div>

      <ul className="space-y-2">
        {MOCK_NOTIFICATIONS.map((n) => (
          <li
            key={n.id}
            className={`rounded-xl border p-4 transition ${
              n.read
                ? "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
                : "border-accent/30 bg-accent/5 dark:border-accent/40 dark:bg-accent/10"
            }`}
          >
            <div className="flex gap-3">
              <span
                className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  n.type === "success"
                    ? "bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-300"
                    : n.type === "error"
                      ? "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300"
                      : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                }`}
              >
                {n.type === "success" ? "✓" : n.type === "error" ? "!" : "i"}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="text-sm font-medium text-slate-900 dark:text-white">{n.title}</p>
                  <span className="text-xs text-slate-500">{n.time}</span>
                </div>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{n.body}</p>
              </div>
              {!n.read ? (
                <span className="h-2 w-2 shrink-0 rounded-full bg-accent" aria-label="Unread" />
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </DashboardShell>
  );
}
