"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";
import { PasswordInput } from "@/components/password-input";
import { api } from "@/lib/api";
import { clearTokens, isLoggedIn, setTokens } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [needsVerify, setNeedsVerify] = useState(false);
  const [resendMsg, setResendMsg] = useState<string | null>(null);
  const [verifyUrl, setVerifyUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) router.replace("/dashboard");
  }, [router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNeedsVerify(false);
    setResendMsg(null);
    setLoading(true);
    try {
      const { data } = await api.post<{
        user: { email: string; email_verified?: boolean };
        tokens: { access_token: string; refresh_token: string };
      }>("/api/v1/auth/login", { email, password });
      setTokens(data.tokens.access_token, data.tokens.refresh_token);
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Login failed";
      setError(msg);
      if (/verify your email/i.test(msg) || /EMAIL_NOT_VERIFIED/i.test(msg)) {
        setNeedsVerify(true);
        clearTokens();
      }
    } finally {
      setLoading(false);
    }
  }

  async function resend() {
    setResendMsg(null);
    setVerifyUrl(null);
    try {
      const { data } = await api.post<{ message: string; verification_url?: string }>(
        "/api/v1/auth/resend-verification-email",
        { email },
      );
      setResendMsg(data.message || "Check your Gmail.");
      if (data.verification_url) setVerifyUrl(data.verification_url);
    } catch (err) {
      setResendMsg(err instanceof Error ? err.message : "Could not resend");
    }
  }

  return (
    <main className="min-h-screen bg-void dark:bg-slate-950">
      <SiteNav />
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:items-center">
        <div className="hidden lg:block">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-teal-700 dark:text-teal-400">
            Welcome back
          </p>
          <h1 className="mt-3 font-display text-4xl text-slate-950 dark:text-white">
            Sign in to ExtractAI
          </h1>
          <p className="mt-4 max-w-md text-slate-600 dark:text-slate-400">
            You must verify your Gmail once after signup before sign-in works.
          </p>
        </div>

        <div className="mx-auto w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-card dark:border-slate-800 dark:bg-slate-900">
          <h2 className="font-display text-2xl text-slate-950 dark:text-white lg:hidden">Sign in</h2>
          <form onSubmit={onSubmit} className="space-y-4 lg:mt-0">
            <label className="block text-left text-xs font-semibold text-slate-700 dark:text-slate-300">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none ring-teal-500/30 focus:ring-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
              />
            </label>
            <label className="block text-left text-xs font-semibold text-slate-700 dark:text-slate-300">
              Password
              <PasswordInput
                required
                value={password}
                onChange={setPassword}
                autoComplete="current-password"
              />
            </label>
            {error ? <p className="text-sm font-medium text-orange-600">{error}</p> : null}
            {needsVerify ? (
              <div className="rounded-lg border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-950 dark:border-teal-900/50 dark:bg-teal-950/40 dark:text-teal-100">
                <p>Open the ExtractAI link in your Gmail, then try again.</p>
                <button
                  type="button"
                  onClick={() => void resend()}
                  className="mt-2 font-semibold text-teal-700 underline dark:text-teal-300"
                >
                  Resend verification email
                </button>
                {resendMsg ? <p className="mt-1 text-xs">{resendMsg}</p> : null}
                {verifyUrl ? (
                  <a
                    href={verifyUrl}
                    className="mt-2 inline-block font-semibold text-teal-800 underline dark:text-teal-200"
                  >
                    Verify email now (skip waiting for Gmail)
                  </a>
                ) : null}
              </div>
            ) : null}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-teal-600 py-2.5 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
            No account?{" "}
            <Link href="/register" className="font-semibold text-teal-700 hover:underline dark:text-teal-400">
              Sign up
            </Link>
          </p>
        </div>
      </div>
      <SiteFooter />
    </main>
  );
}
