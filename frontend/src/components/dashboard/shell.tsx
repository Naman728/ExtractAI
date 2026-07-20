"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import {
  AuthUser,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  isLoggedIn,
} from "@/lib/auth";
import { ThemeToggle } from "@/lib/theme";

type NavItem = {
  label: string;
  href: string;
  icon: React.ReactNode;
};

const NAV: NavItem[] = [
  {
    label: "Overview",
    href: "/dashboard",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path d="M10.707 2.293a1 1 0 0 0-1.414 0l-7 7a1 1 0 0 0 1.414 1.414L4 10.414V17a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1v-2a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1v-6.586l.293.293a1 1 0 0 0 1.414-1.414l-7-7Z" />
      </svg>
    ),
  },
  {
    label: "Projects / Jobs",
    href: "/dashboard#recent-jobs",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path
          fillRule="evenodd"
          d="M2 4.75A.75.75 0 0 1 2.75 4h14.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 4.75ZM2 10a.75.75 0 0 1 .75-.75h14.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 10Zm0 5.25a.75.75 0 0 1 .75-.75h14.5a.75.75 0 0 1 0 1.5H2.75a.75.75 0 0 1-.75-.75Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    label: "Scheduler (preview)",
    href: "/dashboard/scheduler",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm.75-13a.75.75 0 0 0-1.5 0v4c0 .414.336.75.75.75h3a.75.75 0 0 0 0-1.5h-2.25V5Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    label: "Analytics",
    href: "/dashboard/analytics",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path d="M15.5 2A1.5 1.5 0 0 0 14 3.5v13a1.5 1.5 0 0 0 1.5 1.5h1a1.5 1.5 0 0 0 1.5-1.5v-13A1.5 1.5 0 0 0 16.5 2h-1ZM9.5 6A1.5 1.5 0 0 0 8 7.5v9A1.5 1.5 0 0 0 9.5 18h1a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 10.5 6h-1ZM3.5 10A1.5 1.5 0 0 0 2 11.5v5A1.5 1.5 0 0 0 3.5 18h1A1.5 1.5 0 0 0 6 16.5v-5A1.5 1.5 0 0 0 4.5 10h-1Z" />
      </svg>
    ),
  },
  {
    label: "Exports (preview)",
    href: "/dashboard/exports",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path d="M10.75 2.75a.75.75 0 0 0-1.5 0v8.614L6.295 8.235a.75.75 0 1 0-1.09 1.03l4.25 4.5a.75.75 0 0 0 1.09 0l4.25-4.5a.75.75 0 0 0-1.09-1.03l-2.955 3.129V2.75Z" />
        <path d="M3.5 12.75a.75.75 0 0 0-1.5 0v2.5A2.75 2.75 0 0 0 4.75 18h10.5A2.75 2.75 0 0 0 18 15.25v-2.5a.75.75 0 0 0-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5Z" />
      </svg>
    ),
  },
  {
    label: "Team (preview)",
    href: "/dashboard/team",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path d="M10 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM6 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM1.49 15.326a.78.78 0 0 1-.358-.442 3 3 0 0 1 4.308-3.516 6.484 6.484 0 0 0-1.905 3.959c-.023.222-.014.442.025.654a4.97 4.97 0 0 1-2.07-.655ZM16.44 15.98a4.97 4.97 0 0 0 2.07-.654.78.78 0 0 0 .357-.442 3 3 0 0 0-4.308-3.517 6.484 6.484 0 0 1 1.907 3.96 7.464 7.464 0 0 1-.026-.654ZM18 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM5.304 16.19a.844.844 0 0 1-.277-.71 5 5 0 0 1 9.947 0 .843.843 0 0 1-.277.71A6.975 6.975 0 0 1 10 18a6.974 6.974 0 0 1-4.696-1.81Z" />
      </svg>
    ),
  },
  {
    label: "API Keys (preview)",
    href: "/dashboard/api",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-5.5-2.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0ZM10 12a5.99 5.99 0 0 0-4.223 1.715c-.35.35-.094.954.223 1.285C6.47 15.422 8.108 16 10 16s3.53-.578 4.777-1.785c.317-.331.573-.935.223-1.285A5.99 5.99 0 0 0 10 12Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    label: "Notifications",
    href: "/dashboard/notifications",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path d="M10 2a6 6 0 0 0-6 6v3.586l-.707.707A1 1 0 0 0 4 14h12a1 1 0 0 0 .707-1.707L16 11.586V8a6 6 0 0 0-6-6ZM10 18a3 3 0 0 1-3-3h6a3 3 0 0 1-3 3Z" />
      </svg>
    ),
  },
  {
    label: "Settings",
    href: "/dashboard/settings",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
        <path
          fillRule="evenodd"
          d="M7.84 1.804A1 1 0 0 1 8.82 1h2.36a1 1 0 0 1 .98.804l.331 1.652a6.993 6.993 0 0 1 1.929 1.115l1.598-.54a1 1 0 0 1 1.186.447l1.18 2.044a1 1 0 0 1-.205 1.212l-1.278 1.278a6.949 6.949 0 0 1 0 2.828l1.278 1.278a1 1 0 0 1 .205 1.212l-1.18 2.044a1 1 0 0 1-1.186.447l-1.598-.54a6.993 6.993 0 0 1-1.929 1.115l-.331 1.652a1 1 0 0 1-.98.804H8.82a1 1 0 0 1-.98-.804l-.331-1.652a6.993 6.993 0 0 1-1.929-1.115l-1.598.54a1 1 0 0 1-1.186-.447l-1.18-2.044a1 1 0 0 1 .205-1.212l1.278-1.278a6.949 6.949 0 0 1 0-2.828L2.23 6.45a1 1 0 0 1-.205-1.212l1.18-2.044a1 1 0 0 1 1.186-.447l1.598.54A6.993 6.993 0 0 1 7.51 2.804l.331-1.652ZM10 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
];

function NavLink({ item, onNavigate }: { item: NavItem; onNavigate?: () => void }) {
  const pathname = usePathname();
  const active =
    item.href === "/dashboard"
      ? pathname === "/dashboard"
      : pathname === item.href || pathname.startsWith(`${item.href}/`);

  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
        active
          ? "bg-accent/10 text-accent dark:bg-accent/20 dark:text-accent-ice"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
      }`}
    >
      <span className={active ? "text-accent dark:text-accent-ice" : ""}>{item.icon}</span>
      {item.label}
    </Link>
  );
}

function VerifyEmailBanner({ token }: { token: string | null }) {
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function resend() {
    if (!token) return;
    setBusy(true);
    setMsg(null);
    try {
      const { data } = await api.post<{ message: string }>(
        "/api/v1/auth/resend-verification",
        {},
        null,
        token,
      );
      setMsg(data.message || "Verification email sent.");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Could not resend");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-950 dark:border-teal-900/50 dark:bg-teal-950/30 dark:text-teal-100">
      <div>
        <p className="font-semibold">Verify your email</p>
        <p className="mt-0.5 text-teal-900/80 dark:text-teal-100/80">
          Check your inbox for a one-time ExtractAI link.
          {msg ? ` ${msg}` : ""}
        </p>
      </div>
      <button
        type="button"
        disabled={busy || !token}
        onClick={() => void resend()}
        className="rounded-lg bg-teal-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
      >
        {busy ? "Sending…" : "Resend email"}
      </button>
    </div>
  );
}

type DashboardShellProps = {
  children: React.ReactNode;
  title?: string;
  description?: string;
};

export function DashboardShell({ children, title, description }: DashboardShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    setToken(getAccessToken());
    setAuthChecked(true);
  }, [pathname, router]);

  const { data: user } = useQuery({
    queryKey: ["me", token],
    enabled: Boolean(token),
    queryFn: () => api.get<AuthUser>("/api/v1/auth/me", null, token),
  });

  async function signOut() {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await api.post("/api/v1/auth/logout", { refresh_token: refresh });
      }
    } catch {
      // ignore network errors on logout
    }
    clearTokens();
    router.push("/login");
    router.refresh();
  }

  if (!authChecked || !token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-void dark:bg-slate-950">
        <p className="text-sm text-slate-600 dark:text-slate-400">Checking session…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-void dark:bg-slate-950">
      {sidebarOpen ? (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <div className="flex min-h-screen">
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white transition-transform dark:border-slate-800 dark:bg-slate-900 lg:static lg:sticky lg:top-0 lg:z-30 lg:h-screen lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="flex h-14 items-center gap-2 border-b border-slate-200 px-4 dark:border-slate-800">
          <Link href="/" className="font-display text-lg font-semibold text-slate-900 dark:text-white">
            Extract<span className="text-accent">AI</span>
          </Link>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto p-3">
          {NAV.map((item) => (
            <NavLink key={item.href} item={item} onNavigate={() => setSidebarOpen(false)} />
          ))}
        </nav>

        <div className="border-t border-slate-200 p-3 dark:border-slate-800">
          <Link
            href="/"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path
                fillRule="evenodd"
                d="M9.293 2.293a1 1 0 0 1 1.414 0l7 7A1 1 0 0 1 17 11h-1v6a1 1 0 0 1-1 1h-2a1 1 0 0 1-1-1v-3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-6H3a1 1 0 0 1-.707-1.707l7-7Z"
                clipRule="evenodd"
              />
            </svg>
            Back to app
          </Link>
          <button
            type="button"
            onClick={() => void signOut()}
            className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-orange-50 hover:text-orange-700 dark:text-slate-400 dark:hover:bg-orange-950/40 dark:hover:text-orange-300"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path
                fillRule="evenodd"
                d="M3 4.25A2.25 2.25 0 0 1 5.25 2h5.5A2.25 2.25 0 0 1 13 4.25v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 0-.75-.75h-5.5a.75.75 0 0 0-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 0 0 .75-.75v-2a.75.75 0 0 1 1.5 0v2A2.25 2.25 0 0 1 10.75 18h-5.5A2.25 2.25 0 0 1 3 15.75V4.25Z"
                clipRule="evenodd"
              />
              <path
                fillRule="evenodd"
                d="M19 10a.75.75 0 0 0-.75-.75h-6.386l1.318-1.318a.75.75 0 1 0-1.06-1.06l-2.75 2.75a.75.75 0 0 0 0 1.06l2.75 2.75a.75.75 0 1 0 1.06-1.06L11.864 10.75H18.25A.75.75 0 0 0 19 10Z"
                clipRule="evenodd"
              />
            </svg>
            Log out
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-slate-200 bg-white/80 px-4 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80 lg:px-6">
          <button
            type="button"
            aria-label="Open menu"
            className="rounded-lg border border-slate-200 p-2 text-slate-600 transition hover:border-slate-300 lg:hidden dark:border-slate-700 dark:text-slate-300"
            onClick={() => setSidebarOpen(true)}
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path
                fillRule="evenodd"
                d="M2 4.75A.75.75 0 0 1 2.75 4h14.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 4.75ZM2 10a.75.75 0 0 1 .75-.75h14.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 10Zm0 5.25a.75.75 0 0 1 .75-.75h14.5a.75.75 0 0 1 0 1.5H2.75a.75.75 0 0 1-.75-.75Z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          <div className="relative hidden flex-1 sm:block sm:max-w-md">
            <svg
              viewBox="0 0 20 20"
              fill="currentColor"
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            >
              <path
                fillRule="evenodd"
                d="M9 3.5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11ZM2 9a7 7 0 1 1 12.452 4.391l3.328 3.329a.75.75 0 1 1-1.06 1.06l-3.329-3.328A7 7 0 0 1 2 9Z"
                clipRule="evenodd"
              />
            </svg>
            <input
              type="search"
              placeholder="Search jobs, URLs, exports…"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-500 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:placeholder:text-slate-500"
            />
          </div>

          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <Link
              href="/dashboard/notifications"
              className="relative rounded-lg border border-slate-200 p-2 text-slate-600 transition hover:border-slate-300 hover:text-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600 dark:hover:text-white"
              aria-label="Notifications"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path d="M10 2a6 6 0 0 0-6 6v3.586l-.707.707A1 1 0 0 0 4 14h12a1 1 0 0 0 .707-1.707L16 11.586V8a6 6 0 0 0-6-6ZM10 18a3 3 0 0 1-3-3h6a3 3 0 0 1-3 3Z" />
              </svg>
              <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-accent" />
            </Link>

            <ThemeToggle />

            <span
              className="hidden max-w-[12rem] truncate text-sm text-slate-600 sm:inline dark:text-slate-300"
              title={user?.email}
            >
              {user?.email ?? "Account"}
            </span>

            <button
              type="button"
              onClick={() => void signOut()}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:border-orange-300 hover:bg-orange-50 hover:text-orange-700 dark:border-slate-700 dark:text-slate-200 dark:hover:border-orange-800 dark:hover:bg-orange-950/40 dark:hover:text-orange-300"
            >
              Log out
            </button>

            <Link
              href="/"
              className="hidden rounded-lg bg-accent px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-accent-dim sm:inline-flex"
            >
              Extract
            </Link>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8">
          {title ? (
            <div className="mb-8">
              <h1 className="font-display text-2xl font-semibold text-slate-900 dark:text-white sm:text-3xl">
                {title}
              </h1>
              {description ? (
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{description}</p>
              ) : null}
            </div>
          ) : null}
          {user && user.email_verified === false ? (
            <VerifyEmailBanner token={token} />
          ) : null}
          {children}
        </main>
      </div>
      </div>
    </div>
  );
}
