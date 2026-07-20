"use client";

import { useState } from "react";
import Link from "next/link";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";

const sections = [
  {
    id: "getting-started",
    label: "Getting Started",
    content: (
      <>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Getting Started</h2>
        <p className="mt-4 text-slate-600 dark:text-slate-400">
          Create an account, install the browser extension (optional), and run your first extraction in under five
          minutes.
        </p>
        <ol className="mt-6 list-decimal space-y-3 pl-5 text-slate-700 dark:text-slate-300">
          <li>Sign up at ExtractAI and verify your email.</li>
          <li>Create a project and paste a target URL.</li>
          <li>Select fields visually or paste CSS selectors.</li>
          <li>Run a test extraction and review JSON output.</li>
          <li>Schedule recurring runs or call the API.</li>
        </ol>
        <Link
          href="/register"
          className="mt-6 inline-flex rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"
        >
          Create account
        </Link>
      </>
    ),
  },
  {
    id: "api-reference",
    label: "API Reference",
    content: (
      <>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">API Reference</h2>
        <p className="mt-4 text-slate-600 dark:text-slate-400">
          Authenticate with a bearer token and manage jobs programmatically.
        </p>
        <pre className="mt-6 overflow-x-auto rounded-xl bg-slate-950 p-4 font-mono text-sm text-emerald-400">
{`POST /v1/jobs
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "project_id": "proj_abc123",
  "urls": ["https://example.com/listings"],
  "format": "json"
}`}
        </pre>
        <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
          Poll <code className="rounded bg-slate-100 px-1 dark:bg-slate-800">GET /v1/jobs/:id</code> for status or
          configure webhooks for completion events.
        </p>
      </>
    ),
  },
  {
    id: "tutorials",
    label: "Tutorials",
    content: (
      <>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Tutorials</h2>
        <ul className="mt-6 space-y-4">
          {[
            "Scrape paginated product catalogs",
            "Extract JSON-LD and Open Graph metadata",
            "Handle login walls with session cookies",
            "Build a price monitoring dashboard",
          ].map((title) => (
            <li
              key={title}
              className="rounded-lg border border-slate-200 p-4 dark:border-slate-800"
            >
              <h3 className="font-medium text-slate-900 dark:text-slate-100">{title}</h3>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Step-by-step guide · 8–15 min read</p>
            </li>
          ))}
        </ul>
      </>
    ),
  },
  {
    id: "sdk-examples",
    label: "SDK Examples",
    content: (
      <>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">SDK Examples</h2>
        <p className="mt-4 text-slate-600 dark:text-slate-400">Official client libraries for Node.js and Python.</p>
        <pre className="mt-6 overflow-x-auto rounded-xl bg-slate-950 p-4 font-mono text-sm text-emerald-400">
{`import { ExtractAI } from "@extractai/sdk";

const client = new ExtractAI({ apiKey: process.env.EXTRACTAI_KEY });
const job = await client.jobs.create({
  projectId: "proj_abc123",
  urls: ["https://example.com"],
});
console.log(await job.waitUntilDone());`}
        </pre>
      </>
    ),
  },
  {
    id: "integration-guides",
    label: "Integration Guides",
    content: (
      <>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Integration Guides</h2>
        <p className="mt-4 text-slate-600 dark:text-slate-400">
          Connect ExtractAI to your existing tools and data pipelines.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {["Google Sheets", "Slack alerts", "S3 export", "Zapier automations"].map((name) => (
            <div
              key={name}
              className="rounded-lg border border-slate-200 p-4 dark:border-slate-800"
            >
              <h3 className="font-medium text-slate-900 dark:text-slate-100">{name}</h3>
              <p className="mt-1 text-sm text-teal-600 dark:text-teal-400">View guide →</p>
            </div>
          ))}
        </div>
        <Link href="/integrations" className="mt-6 inline-block text-sm font-medium text-teal-600 dark:text-teal-400">
          Browse all integrations
        </Link>
      </>
    ),
  },
  {
    id: "faq",
    label: "FAQ",
    content: (
      <>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">FAQ</h2>
        <dl className="mt-6 space-y-6">
          {[
            {
              q: "Where is data stored?",
              a: "Run results are encrypted at rest in your selected region. Retention follows your plan settings.",
            },
            {
              q: "Can I self-host?",
              a: "Enterprise customers can deploy workers in their VPC. Contact sales for architecture options.",
            },
            {
              q: "Rate limits?",
              a: "API rate limits scale with plan tier. See the dashboard for current quotas and burst allowances.",
            },
          ].map(({ q, a }) => (
            <div key={q}>
              <dt className="font-medium text-slate-900 dark:text-slate-100">{q}</dt>
              <dd className="mt-1 text-sm text-slate-600 dark:text-slate-400">{a}</dd>
            </div>
          ))}
        </dl>
      </>
    ),
  },
];

export default function DocsPage() {
  const [active, setActive] = useState(sections[0].id);
  const panel = sections.find((s) => s.id === active) ?? sections[0];

  return (
    <>
      <SiteNav />
      <main className="min-h-screen bg-white dark:bg-slate-950">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-12 sm:px-6 lg:flex-row">
          <aside className="lg:w-56 lg:shrink-0">
            <nav aria-label="Documentation sections" className="sticky top-24 space-y-1">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Documentation</p>
              {sections.map((section) => (
                <button
                  key={section.id}
                  type="button"
                  onClick={() => setActive(section.id)}
                  aria-current={active === section.id ? "page" : undefined}
                  className={`block w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition ${
                    active === section.id
                      ? "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-400"
                      : "text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-900"
                  }`}
                >
                  {section.label}
                </button>
              ))}
            </nav>
          </aside>

          <article className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50/50 p-6 dark:border-slate-800 dark:bg-slate-900/30 sm:p-8">
            {panel.content}
          </article>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
