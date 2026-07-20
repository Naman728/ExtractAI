"use client";

import Link from "next/link";
import { motion } from "framer-motion";

const PLANS = [
  {
    name: "Free",
    price: "$0",
    blurb: "For trying ExtractAI",
    cta: "Start Free",
    href: "#console",
    popular: false,
    features: [
      "3 website analyses / day",
      "Website Intelligence",
      "Strategy Engine",
      "Network Intelligence",
      "HTML & metadata extraction",
      "JSON export",
      "Community support",
    ],
  },
  {
    name: "Pro",
    price: "$19",
    period: "/month",
    blurb: "Most popular for builders",
    cta: "Upgrade to Pro",
    href: "/register",
    popular: true,
    features: [
      "Unlimited analyses (fair use)",
      "AI Website Understanding",
      "Knowledge Graph",
      "Entity recognition",
      "Browser automation",
      "Scheduled jobs",
      "API access",
      "CSV / Excel / JSON exports",
      "Priority processing",
      "Email support",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    blurb: "Everything in Pro, plus",
    cta: "Contact Sales",
    href: "mailto:sales@extractai.local",
    popular: false,
    features: [
      "Unlimited team members",
      "Custom API limits",
      "Dedicated infrastructure",
      "SSO & audit logs",
      "Webhooks",
      "Bring your own LLM",
      "Private deployments",
      "Dedicated support",
      "Custom integrations",
    ],
  },
];

export function MarketingPricing() {
  return (
    <section id="pricing" className="scroll-mt-24 px-5 py-20 md:px-6 md:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">Pricing</p>
          <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-5xl">Simple, serious pricing</h2>
          <p className="mx-auto mt-4 max-w-xl text-slate-600">
            Start free. Upgrade when AI understanding, automation, and API access become essential.
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          {PLANS.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className={`relative flex flex-col rounded-3xl border p-7 backdrop-blur-xl ${
                plan.popular
                  ? "border-accent/50 bg-gradient-to-b from-accent/10 to-white shadow-[0_0_60px_rgba(56,225,210,0.15)] lg:scale-[1.03]"
                  : "border-slate-200 bg-white"
              }`}
            >
              {plan.popular ? (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-accent px-3 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider text-white">
                  Most popular
                </span>
              ) : null}
              <h3 className="font-display text-2xl text-slate-900">{plan.name}</h3>
              <p className="mt-1 text-sm text-slate-700">{plan.blurb}</p>
              <p className="mt-6 font-display text-4xl text-slate-900">
                {plan.price}
                {plan.period ? (
                  <span className="text-base font-sans text-slate-700">{plan.period}</span>
                ) : null}
              </p>
              <ul className="mt-8 flex-1 space-y-2.5 text-sm text-slate-700">
                {plan.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <span className="text-accent">✓</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                href={plan.href}
                className={`mt-8 block rounded-full py-3 text-center text-sm font-semibold transition ${
                  plan.popular
                    ? "bg-gradient-to-r from-accent to-accent-blue text-white shadow-[0_0_24px_rgba(56,225,210,0.35)]"
                    : "border border-slate-200 text-slate-900 hover:border-accent/40"
                }`}
              >
                {plan.cta}
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
