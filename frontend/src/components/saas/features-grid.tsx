"use client";

import { motion } from "framer-motion";

import {
  IconAi,
  IconApi,
  IconCaptcha,
  IconCloud,
  IconDynamic,
  IconExport,
  IconExtension,
  IconJs,
  IconProxy,
  IconSchedule,
  IconScrape,
  IconTeam,
} from "./illustrations";

const features = [
  {
    icon: IconScrape,
    title: "Universal Web Scraping",
    description:
      "Extract structured data from any public website using visual selectors, CSS paths, or XPath — no boilerplate scripts required.",
  },
  {
    icon: IconDynamic,
    title: "Dynamic Website Support",
    description:
      "Handle infinite scroll, lazy-loaded content, and AJAX-driven listings with built-in wait strategies and DOM mutation tracking.",
  },
  {
    icon: IconJs,
    title: "JavaScript Rendering",
    description:
      "Run headless Chromium sessions to capture data from SPAs and client-rendered pages that static crawlers miss entirely.",
  },
  {
    icon: IconCaptcha,
    title: "CAPTCHA Detection",
    description:
      "Automatic detection of bot challenges with smart retry policies and optional third-party solver integrations when needed.",
  },
  {
    icon: IconAi,
    title: "AI-assisted Data Extraction",
    description:
      "Describe the fields you need in plain language — ExtractAI suggests selectors, validates output, and adapts when layouts change.",
  },
  {
    icon: IconSchedule,
    title: "Scheduling",
    description:
      "Cron-style schedules, interval runs, and webhook triggers keep your datasets fresh without manual intervention.",
  },
  {
    icon: IconCloud,
    title: "Cloud Execution",
    description:
      "Scale from a single page to millions of URLs on managed infrastructure with automatic retries and run history.",
  },
  {
    icon: IconProxy,
    title: "Proxy Management",
    description:
      "Rotate residential and datacenter proxies per request, geo-target regions, and monitor success rates from one dashboard.",
  },
  {
    icon: IconApi,
    title: "API Access",
    description:
      "REST endpoints and webhooks for programmatic control — enqueue jobs, poll status, and stream results into your stack.",
  },
  {
    icon: IconExport,
    title: "Data Export",
    description:
      "Download JSON, CSV, or Excel bundles, push to cloud storage, or pipe directly into spreadsheets and data warehouses.",
  },
  {
    icon: IconExtension,
    title: "Browser Extension Support",
    description:
      "Record selectors in your browser, test extractions locally, and sync projects to the cloud with one click.",
  },
  {
    icon: IconTeam,
    title: "Team Collaboration",
    description:
      "Shared workspaces, role-based permissions, versioned scraper configs, and audit logs for production teams.",
  },
];

export function FeaturesGrid() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-display text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-100 sm:text-4xl">
          Everything you need to extract at scale
        </h2>
        <p className="mt-4 text-slate-600 dark:text-slate-400">
          From quick one-off pulls to enterprise pipelines — built for reliability, observability, and speed.
        </p>
      </div>

      <ul className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature, i) => {
          const Icon = feature.icon;
          return (
            <motion.li
              key={feature.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.04, duration: 0.35 }}
            >
              <article className="group h-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:border-teal-500/30 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-teal-500/40">
                <div className="mb-4 inline-flex rounded-xl bg-teal-50 p-2 text-teal-600 dark:bg-teal-950/50 dark:text-teal-400">
                  <Icon />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                  {feature.description}
                </p>
              </article>
            </motion.li>
          );
        })}
      </ul>
    </section>
  );
}
