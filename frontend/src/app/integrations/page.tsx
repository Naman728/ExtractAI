import Link from "next/link";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";

function MarkChrome() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <circle cx="24" cy="24" r="20" fill="#0D9488" fillOpacity="0.12" />
      <circle cx="24" cy="24" r="14" stroke="#0D9488" strokeWidth="2" fill="none" />
      <circle cx="24" cy="24" r="6" fill="#0D9488" />
    </svg>
  );
}

function MarkFirefox() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <path d="M24 8c8 0 14 6 14 14 0 6-4 11-9 13" stroke="#EA580C" strokeWidth="2" fill="none" strokeLinecap="round" />
      <circle cx="24" cy="24" r="16" stroke="#0D9488" strokeWidth="2" fill="#0D9488" fillOpacity="0.1" />
      <path d="M18 28c3 4 9 4 12 0" stroke="#0D9488" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function MarkSheets() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <rect x="10" y="8" width="28" height="32" rx="3" stroke="#0D9488" strokeWidth="2" fill="#0D9488" fillOpacity="0.08" />
      <path d="M10 16h28M18 8v32" stroke="#0D9488" strokeWidth="1.5" />
      <rect x="22" y="22" width="8" height="6" fill="#0D9488" fillOpacity="0.3" />
    </svg>
  );
}

function MarkCsv() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <rect x="12" y="6" width="24" height="36" rx="2" stroke="currentColor" strokeWidth="2" className="text-slate-400" />
      <text x="24" y="28" textAnchor="middle" fontSize="10" fill="#0D9488" fontFamily="monospace">
        CSV
      </text>
    </svg>
  );
}

function MarkJson() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <rect x="8" y="12" width="32" height="24" rx="3" fill="#0D9488" fillOpacity="0.1" stroke="#0D9488" strokeWidth="2" />
      <path d="M16 24h16M20 20v8M28 20v8" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function MarkApi() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <path d="M8 24h8l4-8 4 16 4-8h8" stroke="#0D9488" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="6" y="34" width="36" height="6" rx="2" fill="#0D9488" fillOpacity="0.2" />
    </svg>
  );
}

function MarkWebhook() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <circle cx="14" cy="24" r="6" stroke="#0D9488" strokeWidth="2" />
      <circle cx="34" cy="16" r="5" stroke="currentColor" strokeWidth="2" className="text-slate-400" />
      <circle cx="34" cy="32" r="5" stroke="currentColor" strokeWidth="2" className="text-slate-400" />
      <path d="M20 22l8-4M20 26l8 4" stroke="#0D9488" strokeWidth="1.5" />
    </svg>
  );
}

function MarkZapier() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <path d="M24 6l4 12h12l-10 8 4 12-10-8-10 8 4-12-10-8h12z" fill="#0D9488" fillOpacity="0.15" stroke="#0D9488" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

function MarkSlack() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <rect x="14" y="8" width="8" height="20" rx="4" fill="#0D9488" />
      <rect x="8" y="14" width="20" height="8" rx="4" fill="#0284C7" />
      <rect x="26" y="20" width="8" height="20" rx="4" fill="#0D9488" fillOpacity="0.6" />
      <rect x="20" y="26" width="20" height="8" rx="4" fill="#0284C7" fillOpacity="0.6" />
    </svg>
  );
}

function MarkNotion() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <rect x="10" y="8" width="28" height="32" rx="3" stroke="currentColor" strokeWidth="2" className="text-slate-500" />
      <path d="M16 16h16M16 24h12M16 32h14" stroke="#0D9488" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function MarkAirtable() {
  return (
    <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
      <path d="M8 14l16-8 16 8-16 8-16-8z" fill="#0D9488" fillOpacity="0.2" stroke="#0D9488" strokeWidth="1.5" />
      <path d="M8 14v20l16 8V22L8 14z" fill="#0284C7" fillOpacity="0.15" stroke="#0284C7" strokeWidth="1.5" />
      <path d="M40 14v20l-16 8V22l16-8z" fill="#0D9488" fillOpacity="0.1" stroke="#0D9488" strokeWidth="1.5" />
    </svg>
  );
}

const integrations = [
  { name: "Chrome Extension", mark: MarkChrome, desc: "Record selectors and sync projects from Chrome." },
  { name: "Firefox Extension", mark: MarkFirefox, desc: "Same workflow for Firefox with native devtools panel." },
  { name: "Google Sheets", mark: MarkSheets, desc: "Push rows directly into spreadsheets on each run." },
  { name: "CSV Export", mark: MarkCsv, desc: "Download flat files or auto-upload to cloud storage." },
  { name: "JSON Pipelines", mark: MarkJson, desc: "Stream newline-delimited JSON to your ETL stack." },
  { name: "REST APIs", mark: MarkApi, desc: "Trigger and monitor jobs from any HTTP client." },
  { name: "Webhooks", mark: MarkWebhook, desc: "Receive run.completed events at your endpoint." },
  { name: "Zapier", mark: MarkZapier, desc: "No-code automations when extractions finish." },
  { name: "Slack", mark: MarkSlack, desc: "Alerts for failures, CAPTCHAs, and quota thresholds." },
  { name: "Notion", mark: MarkNotion, desc: "Append structured records to Notion databases." },
  { name: "Airtable", mark: MarkAirtable, desc: "Sync columns to bases with field mapping." },
];

export default function IntegrationsPage() {
  return (
    <>
      <SiteNav />
      <main className="bg-white dark:bg-slate-950">
        <section className="border-b border-slate-200 px-4 py-16 dark:border-slate-800 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-4xl font-semibold text-slate-900 dark:text-slate-100">
              Integrations
            </h1>
            <p className="mt-4 text-slate-600 dark:text-slate-400">
              Connect ExtractAI to browsers, spreadsheets, APIs, and team tools — all with original connectors built
              for production pipelines.
            </p>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {integrations.map(({ name, mark: Mark, desc }) => (
              <li
                key={name}
                className="rounded-2xl border border-slate-200 bg-white p-6 transition hover:-translate-y-0.5 hover:border-teal-500/30 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50"
              >
                <Mark />
                <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">{name}</h2>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{desc}</p>
                <Link
                  href="/docs"
                  className="mt-4 inline-block text-sm font-medium text-teal-600 hover:text-teal-700 dark:text-teal-400"
                >
                  Setup guide →
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
