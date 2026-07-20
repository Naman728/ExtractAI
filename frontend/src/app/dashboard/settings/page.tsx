"use client";

import { useEffect, useState } from "react";

import { DashboardShell } from "@/components/dashboard/shell";
import { useDashboardSession } from "@/components/dashboard/shared";

export default function SettingsPage() {
  const { user, ready } = useDashboardSession();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [notifications, setNotifications] = useState({
    jobComplete: true,
    jobFailed: true,
    weeklyDigest: false,
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name ?? "");
      setEmail(user.email);
    }
  }, [user]);

  if (!ready) return null;

  return (
    <DashboardShell title="Settings" description="Account preferences and workspace defaults.">
      <form
        className="max-w-xl space-y-8"
        onSubmit={(e) => {
          e.preventDefault();
          setSaved(true);
          setTimeout(() => setSaved(false), 2000);
        }}
      >
        <section className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Profile</h2>
          <label className="mt-4 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Full name
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </label>
          <label className="mt-4 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </label>
          <p className="mt-2 text-xs text-slate-500">Role: {user?.role ?? "member"}</p>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Notifications</h2>
          <div className="mt-4 space-y-3">
            {(
              [
                ["jobComplete", "Job completed"],
                ["jobFailed", "Job failed"],
                ["weeklyDigest", "Weekly digest"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={notifications[key]}
                  onChange={(e) =>
                    setNotifications((n) => ({ ...n, [key]: e.target.checked }))
                  }
                  className="h-4 w-4 rounded border-slate-300 text-accent focus:ring-accent"
                />
                {label}
              </label>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Defaults</h2>
          <label className="mt-4 block text-sm font-medium text-slate-700 dark:text-slate-300">
            Default export format
            <select className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-white">
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
              <option value="ndjson">NDJSON</option>
            </select>
          </label>
        </section>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            className="rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-dim"
          >
            Save changes
          </button>
          {saved ? (
            <span className="text-sm text-teal-600 dark:text-teal-400">Saved (UI preview)</span>
          ) : null}
        </div>
      </form>
    </DashboardShell>
  );
}
