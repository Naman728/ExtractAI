"use client";

import Link from "next/link";
import { useState } from "react";
import { Check, ChevronDown, ChevronUp } from "lucide-react";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";

type BillingCycle = "monthly" | "yearly";

const plans = [
  {
    name: "Free",
    monthly: 0,
    description: "Explore ExtractAI with limited runs and community support.",
    features: ["500 pages / month", "1 active project", "JSON export", "Community support"],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Starter",
    monthly: 29,
    description: "For freelancers and small teams running regular extractions.",
    features: ["25,000 pages / month", "5 active projects", "Scheduling", "Email support"],
    cta: "Start Free Trial",
    highlighted: false,
  },
  {
    name: "Professional",
    monthly: 99,
    description: "Higher limits with JavaScript rendering (Playwright). Proxy pools are planned — not included yet.",
    features: [
      "250,000 pages / month (planned quota)",
      "Unlimited projects",
      "JS rendering (Playwright)",
      "Proxy pool (coming soon)",
      "API access (JWT today; API keys soon)",
      "Priority support",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    monthly: null,
    description: "Custom limits, SSO, dedicated infrastructure, and SLAs.",
    features: ["Custom volume", "SSO / SAML", "Dedicated IPs", "Audit logs", "Solution engineer"],
    cta: "Contact Sales",
    highlighted: false,
  },
];

const comparisonRows = [
  { feature: "Monthly page quota", free: "500", starter: "25K", pro: "250K", enterprise: "Custom" },
  { feature: "JavaScript rendering", free: "—", starter: "—", pro: "✓", enterprise: "✓" },
  { feature: "Proxy rotation", free: "—", starter: "—", pro: "Soon", enterprise: "Soon" },
  { feature: "Scheduling", free: "—", starter: "Soon", pro: "Soon", enterprise: "Soon" },
  { feature: "API & webhooks", free: "REST*", starter: "REST*", pro: "REST*", enterprise: "Custom" },
  { feature: "Team seats", free: "1", starter: "3", pro: "10", enterprise: "Unlimited" },
];

const faqs = [
  {
    q: "Is billing live?",
    a: "Soft launch focuses on extraction jobs, auth, and exports. Stripe billing and plan quotas are not wired yet — pricing cards describe the intended product, not live charges.",
  },
  {
    q: "Can I switch plans anytime?",
    a: "Yes — once billing ships. Upgrades will take effect immediately; downgrades will apply at the next billing cycle.",
  },
  {
    q: "What counts as a page?",
    a: "Each unique URL fetched during a run counts as one page, including pagination and detail views.",
  },
  {
    q: "Is there a free trial on paid plans?",
    a: "Starter and Professional include a 14-day trial with full feature access — no credit card required.",
  },
  {
    q: "Do you offer annual discounts?",
    a: "Yes. Pay yearly and save 20% compared to monthly billing on Starter and Professional.",
  },
];

function price(monthly: number | null, cycle: BillingCycle) {
  if (monthly === null) return "Custom";
  if (cycle === "yearly") {
    const yearly = Math.round(monthly * 12 * 0.8);
    return `$${Math.round(yearly / 12)}`;
  }
  return `$${monthly}`;
}

export default function PricingPage() {
  const [cycle, setCycle] = useState<BillingCycle>("monthly");
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <>
      <SiteNav />
      <main className="bg-white dark:bg-slate-950">
        <section className="border-b border-slate-200 bg-gradient-to-b from-teal-50/50 to-white px-4 py-16 dark:border-slate-800 dark:from-teal-950/20 dark:to-slate-950 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-4xl font-semibold text-slate-900 dark:text-slate-100">
              Simple, transparent pricing
            </h1>
            <p className="mt-4 text-slate-600 dark:text-slate-400">
              Start free, scale when you need to. Every plan includes secure cloud runs and export options.
            </p>

            <div className="mt-8 inline-flex rounded-full border border-slate-200 bg-slate-100 p-1 dark:border-slate-700 dark:bg-slate-900">
              <button
                type="button"
                onClick={() => setCycle("monthly")}
                aria-pressed={cycle === "monthly"}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                  cycle === "monthly"
                    ? "bg-white text-slate-900 shadow dark:bg-slate-800 dark:text-white"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Monthly
              </button>
              <button
                type="button"
                onClick={() => setCycle("yearly")}
                aria-pressed={cycle === "yearly"}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                  cycle === "yearly"
                    ? "bg-white text-slate-900 shadow dark:bg-slate-800 dark:text-white"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                Yearly <span className="text-teal-600 dark:text-teal-400">−20%</span>
              </button>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <div className="grid gap-6 lg:grid-cols-4">
            {plans.map((plan) => (
              <article
                key={plan.name}
                className={`flex flex-col rounded-2xl border p-6 ${
                  plan.highlighted
                    ? "border-teal-500 bg-teal-50/30 shadow-lg dark:border-teal-500/60 dark:bg-teal-950/20"
                    : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/50"
                }`}
              >
                {plan.highlighted ? (
                  <span className="mb-3 w-fit rounded-full bg-teal-600 px-2.5 py-0.5 text-xs font-semibold text-white">
                    Most popular
                  </span>
                ) : null}
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{plan.name}</h2>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{plan.description}</p>
                <p className="mt-4 font-display text-3xl font-semibold text-slate-900 dark:text-slate-100">
                  {price(plan.monthly, cycle)}
                  {plan.monthly !== null ? (
                    <span className="text-base font-normal text-slate-500">/mo</span>
                  ) : null}
                </p>
                {cycle === "yearly" && plan.monthly ? (
                  <p className="text-xs text-teal-600 dark:text-teal-400">Billed annually (20% off)</p>
                ) : null}
                <ul className="mt-6 flex-1 space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex gap-2 text-sm text-slate-700 dark:text-slate-300">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" aria-hidden />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href={plan.name === "Enterprise" ? "/contact" : "/register"}
                  className={`mt-6 block rounded-lg px-4 py-2.5 text-center text-sm font-semibold transition ${
                    plan.highlighted
                      ? "bg-teal-600 text-white hover:bg-teal-700"
                      : "border border-slate-300 text-slate-900 hover:border-teal-500 dark:border-slate-600 dark:text-white"
                  }`}
                >
                  {plan.cta}
                </Link>
              </article>
            ))}
          </div>
        </section>

        <section className="border-t border-slate-200 bg-slate-50 px-4 py-16 dark:border-slate-800 dark:bg-slate-900/30 sm:px-6">
          <div className="mx-auto max-w-5xl overflow-x-auto">
            <h2 className="mb-8 text-center text-2xl font-semibold text-slate-900 dark:text-slate-100">
              Compare plans
            </h2>
            <table className="w-full min-w-[640px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="py-3 pr-4 font-semibold text-slate-900 dark:text-slate-100">Feature</th>
                  <th className="px-4 py-3 font-semibold">Free</th>
                  <th className="px-4 py-3 font-semibold">Starter</th>
                  <th className="px-4 py-3 font-semibold">Pro</th>
                  <th className="px-4 py-3 font-semibold">Enterprise</th>
                </tr>
              </thead>
              <tbody>
                {comparisonRows.map((row) => (
                  <tr key={row.feature} className="border-b border-slate-200 dark:border-slate-800">
                    <td className="py-3 pr-4 text-slate-700 dark:text-slate-300">{row.feature}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{row.free}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{row.starter}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{row.pro}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{row.enterprise}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
          <h2 className="text-center text-2xl font-semibold text-slate-900 dark:text-slate-100">
            Frequently asked questions
          </h2>
          <ul className="mt-8 space-y-3">
            {faqs.map((faq, i) => {
              const open = openFaq === i;
              return (
                <li key={faq.q} className="rounded-xl border border-slate-200 dark:border-slate-800">
                  <button
                    type="button"
                    onClick={() => setOpenFaq(open ? null : i)}
                    aria-expanded={open}
                    className="flex w-full items-center justify-between px-4 py-4 text-left font-medium text-slate-900 dark:text-slate-100"
                  >
                    {faq.q}
                    {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                  {open ? (
                    <p className="border-t border-slate-200 px-4 py-3 text-sm text-slate-600 dark:border-slate-800 dark:text-slate-400">
                      {faq.a}
                    </p>
                  ) : null}
                </li>
              );
            })}
          </ul>
          <div className="mt-12 text-center">
            <Link
              href="/register"
              className="inline-flex rounded-lg bg-teal-600 px-6 py-3 text-sm font-semibold text-white hover:bg-teal-700"
            >
              Create your free account
            </Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
