import Link from "next/link";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";

const values = [
  {
    title: "Reliability first",
    body: "We design for flaky networks, changing DOMs, and real-world anti-bot systems — not demo pages.",
  },
  {
    title: "Transparent ops",
    body: "Every run logs steps, timings, and errors so you can debug without guessing what happened in the cloud.",
  },
  {
    title: "Responsible extraction",
    body: "We help customers respect robots.txt, rate limits, and terms of service while meeting legitimate data needs.",
  },
];

const team = [
  { name: "Alex Rivera", role: "Co-founder & CEO", bio: "Former data platform lead at a market intelligence firm." },
  { name: "Jordan Kim", role: "Co-founder & CTO", bio: "Built large-scale crawlers and browser automation stacks." },
  { name: "Sam Patel", role: "Head of Product", bio: "Focused on visual tooling and developer experience." },
];

export default function AboutPage() {
  return (
    <>
      <SiteNav />
      <main className="bg-white dark:bg-slate-950">
        <section className="border-b border-slate-200 bg-gradient-to-b from-teal-50/40 to-white px-4 py-16 dark:border-slate-800 dark:from-teal-950/20 dark:to-slate-950 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-4xl font-semibold text-slate-900 dark:text-slate-100">
              About ExtractAI
            </h1>
            <p className="mt-4 text-lg text-slate-600 dark:text-slate-400">
              We&apos;re building the extraction layer for the modern web — where sites are dynamic, data is
              unstructured, and teams need answers yesterday.
            </p>
          </div>
        </section>

        <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
          <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Our story</h2>
          <p className="mt-4 leading-relaxed text-slate-600 dark:text-slate-400">
            ExtractAI started when our founders spent too many nights maintaining brittle scrapers for clients whose
            layouts changed weekly. We combined visual selection, headless browsers, and AI-assisted field mapping into
            one platform so analysts and engineers could focus on insights — not selector archaeology.
          </p>
          <p className="mt-4 leading-relaxed text-slate-600 dark:text-slate-400">
            Today we serve ecommerce brands, research teams, and SaaS companies who depend on fresh web data for pricing,
            compliance, and product intelligence.
          </p>
        </section>

        <section className="border-y border-slate-200 bg-slate-50 px-4 py-16 dark:border-slate-800 dark:bg-slate-900/30 sm:px-6">
          <div className="mx-auto max-w-5xl">
            <h2 className="text-center text-2xl font-semibold text-slate-900 dark:text-slate-100">What we believe</h2>
            <ul className="mt-10 grid gap-6 md:grid-cols-3">
              {values.map((v) => (
                <li
                  key={v.title}
                  className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
                >
                  <h3 className="font-semibold text-teal-600 dark:text-teal-400">{v.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{v.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6">
          <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Leadership</h2>
          <ul className="mt-8 grid gap-6 sm:grid-cols-3">
            {team.map((person) => (
              <li key={person.name} className="rounded-2xl border border-slate-200 p-6 dark:border-slate-800">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-teal-100 text-lg font-semibold text-teal-700 dark:bg-teal-950 dark:text-teal-400">
                  {person.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">{person.name}</h3>
                <p className="text-sm text-teal-600 dark:text-teal-400">{person.role}</p>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{person.bio}</p>
              </li>
            ))}
          </ul>
          <div className="mt-12 text-center">
            <Link
              href="/contact"
              className="inline-flex rounded-lg bg-teal-600 px-6 py-3 text-sm font-semibold text-white hover:bg-teal-700"
            >
              Get in touch
            </Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
