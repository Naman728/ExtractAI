"use client";

import { useState, type FormEvent } from "react";
import { Mail, MapPin, MessageSquare } from "lucide-react";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";

export default function ContactPage() {
  const [sent, setSent] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", company: "", message: "" });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSent(true);
    setForm({ name: "", email: "", company: "", message: "" });
  }

  return (
    <>
      <SiteNav />
      <main className="bg-white dark:bg-slate-950">
        <section className="border-b border-slate-200 px-4 py-16 dark:border-slate-800 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-4xl font-semibold text-slate-900 dark:text-slate-100">Contact us</h1>
            <p className="mt-4 text-slate-600 dark:text-slate-400">
              Questions about plans, enterprise deployments, or partnerships — we typically reply within one business day.
            </p>
          </div>
        </section>

        <section className="mx-auto grid max-w-5xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-5">
          <div className="space-y-8 lg:col-span-2">
            <div>
              <div className="flex items-center gap-3 text-teal-600 dark:text-teal-400">
                <Mail className="h-5 w-5" aria-hidden />
                <h2 className="font-semibold text-slate-900 dark:text-slate-100">Email</h2>
              </div>
              <a
                href="mailto:hello@extractai.app"
                className="mt-2 block text-slate-600 hover:text-teal-600 dark:text-slate-400 dark:hover:text-teal-400"
              >
                hello@extractai.app
              </a>
            </div>
            <div>
              <div className="flex items-center gap-3 text-teal-600 dark:text-teal-400">
                <MessageSquare className="h-5 w-5" aria-hidden />
                <h2 className="font-semibold text-slate-900 dark:text-slate-100">Sales</h2>
              </div>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Enterprise volume, custom SLAs, and security reviews.
              </p>
              <a href="mailto:sales@extractai.app" className="text-sm text-teal-600 dark:text-teal-400">
                sales@extractai.app
              </a>
            </div>
            <div>
              <div className="flex items-center gap-3 text-teal-600 dark:text-teal-400">
                <MapPin className="h-5 w-5" aria-hidden />
                <h2 className="font-semibold text-slate-900 dark:text-slate-100">Office</h2>
              </div>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Remote-first team · San Francisco & Bangalore
              </p>
            </div>
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 dark:border-slate-800 dark:bg-slate-900/30 lg:col-span-3"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  Name
                </label>
                <input
                  id="name"
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                />
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                />
              </div>
            </div>
            <div className="mt-4">
              <label htmlFor="company" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Company
              </label>
              <input
                id="company"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              />
            </div>
            <div className="mt-4">
              <label htmlFor="message" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Message
              </label>
              <textarea
                id="message"
                required
                rows={5}
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              />
            </div>
            <button
              type="submit"
              aria-label="Send contact message"
              className="mt-6 rounded-lg bg-teal-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
            >
              Send message
            </button>
            {sent ? (
              <p className="mt-4 text-sm text-teal-600 dark:text-teal-400" role="status">
                Message sent — we&apos;ll be in touch soon.
              </p>
            ) : null}
          </form>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
