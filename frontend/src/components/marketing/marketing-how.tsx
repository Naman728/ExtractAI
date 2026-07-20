"use client";

import { motion } from "framer-motion";

const STEPS = [
  { n: "01", title: "Paste URL", body: "Drop any public URL into the console." },
  { n: "02", title: "Analyze Website", body: "Intelligence profiles stack, CMS, and rendering." },
  { n: "03", title: "Discover APIs", body: "Network intelligence finds JSON and XHR sources." },
  { n: "04", title: "Extract Data", body: "Plugins pull structured fields from the page." },
  { n: "05", title: "Understand with AI", body: "LLMs turn extraction into business knowledge." },
  { n: "06", title: "Export", body: "JSON, CSV, Excel — or consume via API." },
];

export function MarketingHow() {
  return (
    <section id="how" className="scroll-mt-24 px-5 py-20 md:px-6 md:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 max-w-2xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">How it works</p>
          <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-5xl">
            From URL to structured knowledge
          </h2>
        </div>

        <div className="relative">
          <div className="pointer-events-none absolute left-0 right-0 top-10 hidden h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent lg:block" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
            {STEPS.map((s, i) => (
              <motion.div
                key={s.n}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07 }}
                whileHover={{ y: -6 }}
                className="relative rounded-2xl border border-slate-200 bg-white p-4 backdrop-blur"
              >
                <span className="font-mono text-xs text-accent">{s.n}</span>
                <h3 className="mt-3 font-medium text-slate-900">{s.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-700">{s.body}</p>
                {i < STEPS.length - 1 ? (
                  <span className="absolute -right-2 top-10 hidden text-accent/50 lg:block">→</span>
                ) : null}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
