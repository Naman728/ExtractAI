"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";
import { PasswordInput } from "@/components/password-input";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [pendingVerify, setPendingVerify] = useState<{
    message: string;
    emailSent: boolean;
    verificationUrl?: string;
  } | null>(null);
  const [resendMsg, setResendMsg] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post<{
        email_sent?: boolean;
        message?: string;
        verification_required?: boolean;
        verification_url?: string;
      }>("/api/v1/auth/register", {
        email,
        password,
        full_name: fullName || null,
      });
      setPendingVerify({
        message:
          data.message ||
          "Check your Gmail for a one-time ExtractAI verification link, then sign in.",
        emailSent: Boolean(data.email_sent),
        verificationUrl: data.verification_url,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  async function resend() {
    setResendMsg(null);
    try {
      const { data } = await api.post<{ message: string; verification_url?: string }>(
        "/api/v1/auth/resend-verification-email",
        { email },
      );
      setResendMsg(data.message || "Email sent.");
      if (data.verification_url) {
        setPendingVerify((prev) =>
          prev ? { ...prev, verificationUrl: data.verification_url } : prev,
        );
      }
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
            Get started
          </p>
          <h1 className="mt-3 font-display text-4xl text-slate-950 dark:text-white">
            Create your ExtractAI account
          </h1>
          <ul className="mt-6 space-y-3 text-sm text-slate-600 dark:text-slate-400">
            <li>• Verify once via Gmail before you can sign in</li>
            <li>• Job history & larger batches</li>
            <li>• Ready-made JSON exports</li>
          </ul>
        </div>
        <div className="mx-auto w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-card dark:border-slate-800 dark:bg-slate-900">
          {pendingVerify ? (
            <div>
              <h2 className="font-display text-2xl text-slate-950 dark:text-white">
                Check your Gmail
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                We sent a one-time link to{" "}
                <strong className="text-slate-900 dark:text-white">{email}</strong>. Open it to
                verify, then sign in. You cannot access the app until that step is done.
              </p>
              <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">{pendingVerify.message}</p>
              {!pendingVerify.emailSent ? (
                <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-100">
                  Mail delivery failed on our side. Add Gmail SMTP settings on the API
                  (Render), redeploy, then resend below.
                </p>
              ) : (
                <p className="mt-3 text-xs text-slate-500">Also check Spam / Promotions.</p>
              )}
              {pendingVerify.verificationUrl ? (
                <a
                  href={pendingVerify.verificationUrl}
                  className="mt-4 block w-full rounded-xl bg-teal-600 py-2.5 text-center text-sm font-semibold text-white hover:bg-teal-700"
                >
                  Verify email now
                </a>
              ) : null}
              <button
                type="button"
                onClick={() => void resend()}
                className="mt-4 w-full rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-800 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-100 dark:hover:bg-slate-800"
              >
                Resend verification email
              </button>
              {resendMsg ? <p className="mt-2 text-sm text-teal-700 dark:text-teal-400">{resendMsg}</p> : null}
              <Link
                href="/login"
                className="mt-6 block w-full rounded-xl bg-teal-600 py-2.5 text-center text-sm font-semibold text-white hover:bg-teal-700"
              >
                Go to sign in
              </Link>
            </div>
          ) : (
            <>
              <h2 className="font-display text-2xl text-slate-950 dark:text-white">Sign up</h2>
              <form onSubmit={onSubmit} className="mt-6 space-y-4">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Full name
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none ring-teal-500/30 focus:ring-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                    placeholder="Optional"
                  />
                </label>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Gmail / email
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none ring-teal-500/30 focus:ring-2 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                  />
                </label>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Password
                  <PasswordInput
                    required
                    minLength={8}
                    value={password}
                    onChange={setPassword}
                    autoComplete="new-password"
                  />
                </label>
                {error ? <p className="text-sm font-medium text-orange-600">{error}</p> : null}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-xl bg-teal-600 py-2.5 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
                >
                  {loading ? "Creating…" : "Create account"}
                </button>
              </form>
              <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
                Already have an account?{" "}
                <Link href="/login" className="font-semibold text-teal-700 hover:underline dark:text-teal-400">
                  Sign in
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
      <SiteFooter />
    </main>
  );
}
