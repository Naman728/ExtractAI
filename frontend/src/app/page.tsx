"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, Play, Sparkles } from "lucide-react";

import { AnalyzeForm } from "@/components/landing/analyze-form";
import { FeaturesGrid } from "@/components/saas/features-grid";
import { HeroMockup } from "@/components/saas/hero-mockup";
import { ProductShowcase } from "@/components/saas/product-showcase";
import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";

const STEPS = [
  {
    n: "01",
    title: "Paste any URL",
    body: "Drop a public page, listing, or app route. ExtractAI profiles the site before it scrapes.",
  },
  {
    n: "02",
    title: "Watch the orchestra",
    body: "Intelligence, strategy, fetch, plugins, and AI understanding run as a live pipeline.",
  },
  {
    n: "03",
    title: "Copy ready-made JSON",
    body: "Every product, book, or official arrives as one dictionary — paste straight into your project.",
  },
  {
    n: "04",
    title: "Automate in the cloud",
    body: "Schedule jobs, call the API, export CSV/JSON/XLSX, and pipe results into Sheets or webhooks.",
  },
];

const METRICS = [
  { value: "99.2%", label: "Job success rate" },
  { value: "22+", label: "Extraction plugins" },
  { value: "<3s", label: "Typical static pages" },
  { value: "Ready JSON", label: "Project-paste exports" },
];

const REVIEWS = [
  {
    quote:
      "We replaced three brittle scrapers with ExtractAI. The ready-made JSON is exactly what our backend expects.",
    name: "Priya N.",
    role: "Data Engineer",
  },
  {
    quote:
      "The live orchestra view finally makes pipeline debugging understandable for non-engineers on our team.",
    name: "Marcus L.",
    role: "Product Ops",
  },
  {
    quote:
      "BallotReady batches and generic e-commerce sites both land as clean entity dicts. Huge time saver.",
    name: "Elena R.",
    role: "Founder",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-void text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <SiteNav />

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-200 dark:border-slate-800">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(13,148,136,0.18),transparent),radial-gradient(ellipse_40%_40%_at_90%_10%,rgba(2,132,199,0.12),transparent)]"
        />
        <div className="relative mx-auto grid max-w-6xl gap-12 px-4 pb-20 pt-16 sm:px-6 lg:grid-cols-2 lg:items-center lg:pt-20">
          <div>
            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800 dark:border-teal-800 dark:bg-teal-950/50 dark:text-teal-200"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Intelligent web data extraction
            </motion.p>
            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="mt-5 font-display text-4xl font-semibold tracking-tight text-slate-950 dark:text-white md:text-5xl lg:text-[3.25rem] lg:leading-[1.1]"
            >
              ExtractAI
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mt-3 text-xl font-medium text-slate-700 dark:text-slate-300 md:text-2xl"
            >
              Powerful scraping for teams that ship structured data
            </motion.p>
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="mt-4 max-w-xl text-base leading-relaxed text-slate-600 dark:text-slate-400"
            >
              Profile any site, pick the best strategy, render JavaScript when needed, and return
              entities as copy-paste-ready JSON — with a live pipeline orchestra you can trust.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-8 flex flex-wrap gap-3"
            >
              <a
                href="#console"
                className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-teal-600/20 transition hover:bg-teal-700"
              >
                Start free <ArrowRight className="h-4 w-4" />
              </a>
              <Link
                href="/pricing"
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 transition hover:border-teal-500 hover:text-teal-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              >
                View pricing
              </Link>
              <Link
                href="/docs"
                className="inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold text-slate-600 hover:text-teal-700 dark:text-slate-300"
              >
                <Play className="h-4 w-4" /> Docs
              </Link>
            </motion.div>
            <p className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-medium text-slate-500 dark:text-slate-400">
              <span className="inline-flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-600" /> Guest extractions free
              </span>
              <span className="inline-flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-600" /> No credit card
              </span>
              <span className="inline-flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-600" /> Ready-made export
              </span>
            </p>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.5 }}
            className="lg:pl-4"
          >
            <HeroMockup />
          </motion.div>
        </div>
      </section>

      {/* Metrics */}
      <section className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-4 py-10 sm:px-6 md:grid-cols-4">
          {METRICS.map((m) => (
            <div key={m.label} className="text-center md:text-left">
              <p className="font-display text-2xl font-semibold text-teal-700 dark:text-teal-400 md:text-3xl">
                {m.value}
              </p>
              <p className="mt-1 text-sm font-medium text-slate-600 dark:text-slate-400">{m.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Live console */}
      <section id="console" className="scroll-mt-24 border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-teal-700 dark:text-teal-400">
              Try it live
            </p>
            <h2 className="mt-3 font-display text-3xl text-slate-950 dark:text-white md:text-4xl">
              Scrape your first site in minutes
            </h2>
            <p className="mt-3 text-slate-600 dark:text-slate-400">
              Paste a URL — optional address or query inputs unlock browser-agent workflows.
            </p>
          </div>
          <div className="mx-auto mt-10 max-w-3xl rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900 sm:p-8">
            <AnalyzeForm />
          </div>
        </div>
      </section>

      {/* Interactive product demos — WebScraper-style explainers */}
      <ProductShowcase />

      {/* Features */}
      <section id="features" className="scroll-mt-24 border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <div className="mx-auto max-w-2xl text-center">
            <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-teal-700 dark:text-teal-400">
              Features
            </p>
            <h2 className="mt-3 font-display text-3xl text-slate-950 dark:text-white md:text-4xl">
              Everything you need to extract at scale
            </h2>
            <p className="mt-3 text-slate-600 dark:text-slate-400">
              Cloud execution, proxies, scheduling, AI understanding, and exports — built for
              production teams.
            </p>
          </div>
          <div className="mt-12">
            <FeaturesGrid />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <h2 className="font-display text-3xl text-slate-950 dark:text-white md:text-4xl">
            Get started in 4 steps
          </h2>
          <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s) => (
              <div key={s.n} className="relative rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
                <span className="font-mono text-xs font-bold text-teal-600">{s.n}</span>
                <h3 className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{s.title}</h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <h2 className="font-display text-3xl text-slate-950 dark:text-white md:text-4xl">
            Trusted by builders who hate brittle scrapers
          </h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {REVIEWS.map((r) => (
              <blockquote
                key={r.name}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-800 dark:bg-slate-950"
              >
                <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                  “{r.quote}”
                </p>
                <footer className="mt-4">
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{r.name}</p>
                  <p className="text-xs text-slate-500">{r.role}</p>
                </footer>
              </blockquote>
            ))}
          </div>
          <div className="mt-12 flex flex-wrap items-center justify-center gap-8 opacity-70 grayscale">
            {["Northwind", "Acme Labs", "Cedar Co", "Orbit Data", "Helix"].map((name) => (
              <span
                key={name}
                className="font-display text-lg font-semibold tracking-tight text-slate-500 dark:text-slate-400"
              >
                {name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-teal-700 to-sky-800 px-8 py-12 text-center text-white shadow-xl md:px-16">
            <h2 className="font-display text-3xl md:text-4xl">Start extracting with ExtractAI</h2>
            <p className="mx-auto mt-3 max-w-xl text-teal-50">
              Free guest runs today. Upgrade when you need history, batches, scheduling, and API
              access.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <a
                href="#console"
                className="rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-teal-800 hover:bg-teal-50"
              >
                Try free
              </a>
              <Link
                href="/register"
                className="rounded-lg border border-white/40 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/10"
              >
                Create account
              </Link>
            </div>
          </div>
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}
