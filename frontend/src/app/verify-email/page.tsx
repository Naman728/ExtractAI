"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";
import { api } from "@/lib/api";

function VerifyEmailInner() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [message, setMessage] = useState("Verifying your email…");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Missing verification token.");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await api.post("/api/v1/auth/verify-email", { token });
        if (cancelled) return;
        setStatus("ok");
        setMessage("Email verified. You can now sign in with your password.");
      } catch (err) {
        if (cancelled) return;
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Verification failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-teal-700 dark:text-teal-400">
        ExtractAI
      </p>
      <h1 className="mt-2 font-display text-2xl text-slate-950 dark:text-white">
        {status === "ok" ? "You’re verified" : status === "error" ? "Verification issue" : "Verifying…"}
      </h1>
      <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">{message}</p>
      <div className="mt-6 flex flex-col gap-2">
        {status === "ok" ? (
          <Link
            href="/login"
            className="w-full rounded-xl bg-teal-600 py-2.5 text-center text-sm font-semibold text-white hover:bg-teal-700"
          >
            Sign in
          </Link>
        ) : null}
        <Link
          href="/login"
          className="text-center text-sm font-semibold text-teal-700 hover:underline dark:text-teal-400"
        >
          Back to sign in
        </Link>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <main className="min-h-screen bg-void dark:bg-slate-950">
      <SiteNav />
      <div className="mx-auto flex max-w-6xl justify-center px-4 py-16 sm:px-6">
        <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
          <VerifyEmailInner />
        </Suspense>
      </div>
      <SiteFooter />
    </main>
  );
}
