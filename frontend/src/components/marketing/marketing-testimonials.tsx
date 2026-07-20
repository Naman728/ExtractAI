"use client";

import { motion } from "framer-motion";

const QUOTES = [
  {
    role: "Developer",
    quote:
      "ExtractAI replaced three brittle scrapers with one pipeline that actually understands the site.",
    name: "Jordan Lee",
  },
  {
    role: "Startup Founder",
    quote:
      "We ship website intelligence into our product without babysitting selectors every week.",
    name: "Priya Nair",
  },
  {
    role: "Data Engineer",
    quote: "Network discovery alone paid for Pro — we finally see the APIs the page was calling.",
    name: "Marcus Chen",
  },
  {
    role: "AI Researcher",
    quote: "Structured extraction plus knowledge graphs is the right layer under agent workflows.",
    name: "Elena Vogt",
  },
  {
    role: "Marketing Team",
    quote: "Competitive pages become clean JSON we can feed into reports the same day.",
    name: "Sam Ortiz",
  },
];

export function MarketingTestimonials() {
  return (
    <section className="px-5 py-20 md:px-6 md:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="mb-4 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">Testimonials</p>
          <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-4xl">Trusted by builders</h2>
          <p className="mt-3 text-xs text-slate-700">Sample content for design preview — fictional quotes.</p>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {QUOTES.map((q, i) => (
            <motion.blockquote
              key={q.name}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              className="rounded-2xl border border-slate-200 bg-white p-6 backdrop-blur"
            >
              <p className="text-sm leading-relaxed text-slate-700">&ldquo;{q.quote}&rdquo;</p>
              <footer className="mt-5">
                <p className="text-sm text-slate-900">{q.name}</p>
                <p className="text-xs text-slate-700">{q.role}</p>
              </footer>
            </motion.blockquote>
          ))}
        </div>
      </div>
    </section>
  );
}
