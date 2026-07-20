"use client";

import { motion } from "framer-motion";

const FEATURES = [
  {
    title: "Website Intelligence",
    body: "Automatically profiles frameworks, CMS, rendering, robots, metadata, and architecture.",
  },
  {
    title: "Universal Extraction",
    body: "Extract headings, products, tables, emails, phones, JSON-LD, OpenGraph, and more.",
  },
  {
    title: "Network Intelligence",
    body: "Discover REST APIs, GraphQL endpoints, XHR requests, JSON resources, and assets.",
  },
  {
    title: "Strategy Engine",
    body: "Automatically selects the fastest and most accurate extraction strategy.",
  },
  {
    title: "Browser Automation",
    body: "Supports dynamic websites with Playwright and intelligent browser execution.",
  },
  {
    title: "AI Understanding",
    body: "Convert extracted data into structured business knowledge using LLMs.",
  },
  {
    title: "Knowledge Graph",
    body: "Generate semantic relationships between entities, products, organizations, and people.",
  },
  {
    title: "Exports",
    body: "CSV, Excel, JSON today — PDF on the roadmap. Every job is API-ready.",
  },
  {
    title: "API Ready",
    body: "Every extraction can be consumed by your applications, agents, and workflows.",
  },
];

export function MarketingFeatures() {
  return (
    <section id="features" className="scroll-mt-24 px-5 py-20 md:px-6 md:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 max-w-2xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">Why ExtractAI</p>
          <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-5xl">
            An AI operating system for websites
          </h2>
          <p className="mt-4 text-slate-600">
            Not a brittle scraper. A layered platform that profiles, strategizes, extracts, and
            understands.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.article
              key={f.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ delay: (i % 3) * 0.06 }}
              whileHover={{ y: -4, borderColor: "rgba(56,225,210,0.35)" }}
              className="group rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-transparent p-6 backdrop-blur-sm"
            >
              <div className="mb-4 h-px w-10 bg-gradient-to-r from-accent to-transparent transition group-hover:w-16" />
              <h3 className="font-display text-xl text-slate-900">{f.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">{f.body}</p>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
