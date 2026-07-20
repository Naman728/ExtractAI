"use client";

import { DashboardShell } from "@/components/dashboard/shell";
import { ComingSoonBanner } from "@/components/dashboard/coming-soon-banner";
import { useDashboardSession } from "@/components/dashboard/shared";

const MOCK_TEAM = [
  { id: "1", name: "You", email: "owner@extractai.dev", role: "Owner", status: "active" },
  { id: "2", name: "Alex Chen", email: "alex@company.com", role: "Editor", status: "active" },
  { id: "3", name: "Sam Rivera", email: "sam@company.com", role: "Viewer", status: "invited" },
];

export default function TeamPage() {
  const { user, ready } = useDashboardSession();

  if (!ready) return null;

  const seatsUsed = MOCK_TEAM.length;
  const seatLimit = 5;

  return (
    <DashboardShell title="Team" description="Manage seats, roles, and workspace access.">
      <ComingSoonBanner
        feature="Team seats"
        detail="Team invites and roles are not live yet. Soft launch is single-user accounts only."
      />
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div>
          <p className="text-sm text-slate-600 dark:text-slate-400">Seats used</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">
            {seatsUsed} <span className="text-base font-normal text-slate-500">/ {seatLimit}</span>
          </p>
        </div>
        <div className="h-2 w-full max-w-xs overflow-hidden rounded-full bg-slate-100 sm:w-48 dark:bg-slate-800">
          <div
            className="h-full rounded-full bg-accent"
            style={{ width: `${(seatsUsed / seatLimit) * 100}%` }}
          />
        </div>
        <button
          type="button"
          className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-dim"
        >
          Invite member
        </button>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
          <thead className="bg-slate-50 dark:bg-slate-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Member
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Role
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {MOCK_TEAM.map((member) => (
              <tr key={member.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-slate-900 dark:text-white">
                    {member.email === user?.email ? user.email : member.name}
                  </p>
                  <p className="text-xs text-slate-500">{member.email}</p>
                </td>
                <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">{member.role}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                      member.status === "active"
                        ? "bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-300"
                        : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                    }`}
                  >
                    {member.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
        Team billing and SSO integrations are planned for a future release.
      </p>
    </DashboardShell>
  );
}
