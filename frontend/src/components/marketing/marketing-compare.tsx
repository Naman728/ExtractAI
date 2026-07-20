"use client";

import { motion } from "framer-motion";

const ROWS = [
  { feature: "HTML & metadata extraction", free: true, pro: true, ent: true },
  { feature: "Website & network intelligence", free: true, pro: true, ent: true },
  { feature: "Daily job limits", free: "3 / day", pro: "Fair use", ent: "Custom" },
  { feature: "AI Understanding", free: false, pro: true, ent: true },
  { feature: "Knowledge Graph", free: false, pro: true, ent: true },
  { feature: "Browser automation", free: false, pro: true, ent: true },
  { feature: "API access", free: false, pro: true, ent: true },
  { feature: "Priority queue", free: false, pro: true, ent: true },
  { feature: "SSO & audit logs", free: false, pro: false, ent: true },
  { feature: "Bring your own LLM", free: false, pro: false, ent: true },
  { feature: "Private deployments", free: false, pro: false, ent: true },
];

function Cell({ v }: { v: boolean | string }) {
  if (typeof v === "string") return <span className="text-slate-700">{v}</span>;
  return v ? <span className="text-accent">✓</span> : <span className="text-slate-600">—</span>;
}

export function MarketingCompare() {
  return (
    <section className="px-5 py-16 md:px-6 md:py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">Why upgrade</p>
          <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-4xl">Compare plans at a glance</h2>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="overflow-x-auto rounded-2xl border border-slate-200 bg-white backdrop-blur"
        >
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-700">
                <th className="px-5 py-4 font-medium">Capability</th>
                <th className="px-5 py-4 font-medium">Free</th>
                <th className="px-5 py-4 font-medium text-accent">Pro</th>
                <th className="px-5 py-4 font-medium">Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((r) => (
                <tr key={r.feature} className="border-b border-slate-100 text-slate-700">
                  <td className="px-5 py-3.5 text-slate-900">{r.feature}</td>
                  <td className="px-5 py-3.5">
                    <Cell v={r.free} />
                  </td>
                  <td className="px-5 py-3.5">
                    <Cell v={r.pro} />
                  </td>
                  <td className="px-5 py-3.5">
                    <Cell v={r.ent} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      </div>
    </section>
  );
}
