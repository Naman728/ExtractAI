"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

const FAQS = [
  {
    q: "Does ExtractAI use AI to scrape pages?",
    a: "No. Extraction runs first with deterministic engines. AI Understanding runs after extraction to summarize, classify, and build knowledge graphs from structured data.",
  },
  {
    q: "What’s included in Free vs Pro?",
    a: "Free covers intelligence, strategy, network discovery, and core HTML/metadata extraction with daily limits. Pro unlocks AI understanding, knowledge graphs, browser automation, API access, and higher throughput.",
  },
  {
    q: "When is browser automation used?",
    a: "When you provide interactive inputs (search, address, topics) or the strategy engine detects a dynamic site that needs Playwright. Static and API-friendly sites use faster fetch paths.",
  },
  {
    q: "Which websites are supported?",
    a: "ExtractAI is designed for public websites across SaaS, e-commerce, docs, news, government, and more. Always respect each site’s terms and robots.txt. We do not encourage prohibited automation.",
  },
  {
    q: "What export formats are available?",
    a: "JSON is available on Free. Pro adds CSV and Excel exports for owned jobs. PDF is on the roadmap.",
  },
  {
    q: "How do you handle security?",
    a: "API keys stay in server environment variables. Jobs are scoped to the owning user or guest session. Enterprise adds SSO, audit logs, and private deployment options.",
  },
  {
    q: "Is there an API?",
    a: "Yes — jobs, results, intelligence, network, and batches are exposed over REST. Pro unlocks production API usage; Enterprise adds custom limits and webhooks.",
  },
  {
    q: "Which LLMs can I use?",
    a: "The platform supports OpenAI, Gemini, Anthropic, and Ollama via configuration. Enterprise can bring your own LLM keys and private models.",
  },
];

export function MarketingFaq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section className="px-5 py-20 md:px-6 md:py-28">
      <div className="mx-auto max-w-3xl">
        <div className="mb-10 text-center">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">FAQ</p>
          <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-4xl">Questions, answered</h2>
        </div>

        <div className="space-y-3">
          {FAQS.map((item, i) => {
            const isOpen = open === i;
            return (
              <div key={item.q} className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
                <button
                  type="button"
                  className="flex w-full items-center justify-between px-5 py-4 text-left"
                  onClick={() => setOpen(isOpen ? null : i)}
                >
                  <span className="pr-4 text-sm font-medium text-slate-900 md:text-base">{item.q}</span>
                  <span className="text-accent">{isOpen ? "−" : "+"}</span>
                </button>
                <AnimatePresence initial={false}>
                  {isOpen ? (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                    >
                      <p className="border-t border-slate-200 px-5 py-4 text-sm leading-relaxed text-slate-600">
                        {item.a}
                      </p>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
