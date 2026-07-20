"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import {
  AuthUser,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  getValidAccessToken,
  isLoggedIn,
} from "@/lib/auth";

type SiteHeaderProps = {
  variant?: "landing" | "app";
};

export function SiteHeader({ variant = "app" }: SiteHeaderProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  const refreshUser = useCallback(async () => {
    const token = await getValidAccessToken();
    if (!token) {
      setUser(null);
      setReady(true);
      return;
    }
    try {
      const me = await api.get<AuthUser>("/api/v1/auth/me", null, token);
      setUser(me);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser, pathname]);

  async function signOut() {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await api.post("/api/v1/auth/logout", { refresh_token: refresh });
      }
    } catch {
      // ignore
    }
    clearTokens();
    setUser(null);
    router.push("/");
    router.refresh();
  }

  const loggedIn = ready && (user != null || isLoggedIn());

  return (
    <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
      <Link href="/" className="font-display text-2xl font-semibold tracking-tight text-slate-900">
        Extract<span className="text-accent">AI</span>
      </Link>
      <nav className="flex flex-wrap items-center justify-end gap-3 text-sm font-medium text-slate-700 sm:gap-4">
        {variant === "landing" ? (
          <>
            <Link href="/intelligence" className="transition hover:text-slate-950">
              Intelligence
            </Link>
            <Link href="/strategy" className="hidden transition hover:text-slate-950 sm:inline">
              Strategy
            </Link>
            <Link href="/network" className="hidden transition hover:text-slate-950 sm:inline">
              Network
            </Link>
          </>
        ) : null}

        {!ready ? (
          <span className="text-slate-600">…</span>
        ) : loggedIn ? (
          <>
            <Link
              href="/dashboard"
              className={`transition hover:text-slate-950 ${pathname === "/dashboard" ? "text-slate-900" : ""}`}
            >
              Dashboard
            </Link>
            <Link href="/#console" className="transition hover:text-slate-950">
              New extract
            </Link>
            <span className="hidden max-w-[10rem] truncate text-slate-700 sm:inline" title={user?.email}>
              {user?.email ?? "Account"}
            </span>
            <button
              type="button"
              onClick={() => void signOut()}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-medium text-slate-700 transition hover:border-slate-300 hover:text-slate-950"
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="transition hover:text-slate-950">
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded-lg bg-accent px-3 py-1.5 font-medium text-white transition hover:bg-accent-dim"
            >
              Sign up
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}
