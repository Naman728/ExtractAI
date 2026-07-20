"use client";

import { motion } from "framer-motion";

const CATEGORIES = [
  "Amazon-class retail",
  "Shopify storefronts",
  "Next.js apps",
  "WordPress sites",
  "Wikipedia & knowledge",
  "Government portals",
  "News publishers",
  "Blogs & media",
  "Universities",
  "Documentation",
  "SaaS products",
  "E-commerce",
  "Portfolios",
  "Corporate sites",
  "Marketplaces",
];

export function MarketingSupported() {
  return (
    <section id="solutions" className="scroll-mt-24 px-5 py-20 md:px-6 md:py-24">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">Designed for</p>
          <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-4xl">
            Site categories & technologies
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-sm text-slate-600">
            Examples of site types and stacks ExtractAI is built to analyze. We do not encourage
            automation that violates a site&apos;s terms — always respect robots.txt and applicable law.
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-3">
          {CATEGORIES.map((c, i) => (
            <motion.span
              key={c}
              initial={{ opacity: 0, scale: 0.92 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.03 }}
              whileHover={{ borderColor: "rgba(56,225,210,0.5)", y: -2 }}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 backdrop-blur"
            >
              {c}
            </motion.span>
          ))}
        </div>
      </div>
    </section>
  );
}
