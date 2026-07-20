"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

const STAGES = [
  { id: "intel", label: "Website Intelligence", detail: "Next.js · SSR · robots.txt" },
  { id: "strategy", label: "Strategy Engine", detail: "Selected: metadata + plugins" },
  { id: "network", label: "Network Intelligence", detail: "12 XHR · 3 JSON endpoints" },
  { id: "extract", label: "Extraction", detail: "Title · products · emails · JSON-LD" },
  { id: "ai", label: "AI Understanding", detail: "Category: SaaS · conf 92%" },
  { id: "json", label: "Structured JSON", detail: "schema_version: 1 · ready" },
];

const SAMPLE_JSON = `{
  "title": "Acme Analytics",
  "category": "SaaS",
  "products": ["Insights Pro"],
  "emails": ["hello@acme.dev"],
  "apis": ["/api/v1/metrics"],
  "confidence": 0.92
}`;

export function MarketingDemo() {
  const [stage, setStage] = useState(0);
  const [typed, setTyped] = useState("");
  const url = "https://acme.dev";

  useEffect(() => {
    let i = 0;
    setTyped("");
    const type = setInterval(() => {
      i += 1;
      setTyped(url.slice(0, i));
      if (i >= url.length) clearInterval(type);
    }, 55);
    return () => clearInterval(type);
  }, []);

  useEffect(() => {
    const t = setInterval(() => {
      setStage((s) => (s + 1) % STAGES.length);
    }, 1800);
    return () => clearInterval(t);
  }, []);

  const progress = ((stage + 1) / STAGES.length) * 100;

  return (
    <section id="demo" className="scroll-mt-24 px-5 py-20 md:px-6 md:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 max-w-2xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">Live product demo</p>
          <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-5xl">Watch the pipeline think</h2>
          <p className="mt-4 text-slate-600">
            An interactive preview of ExtractAI&apos;s operating system for websites — from URL paste to
            structured knowledge. Illustrative sample data.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-2xl shadow-slate-200/80 backdrop-blur-xl md:p-7">
            <div className="mb-5 flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-red-400/80" />
              <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
              <span className="ml-3 font-mono text-xs text-slate-700">extractai — pipeline</span>
            </div>

            <div className="mb-6 rounded-xl border border-slate-200 bg-void/70 px-4 py-3 font-mono text-sm text-accent">
              {typed}
              <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-accent align-middle" />
            </div>

            <div className="mb-6 h-1.5 overflow-hidden rounded-full bg-slate-100">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-accent to-accent-blue"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.45 }}
              />
            </div>

            <div className="space-y-2.5">
              {STAGES.map((s, i) => {
                const active = i === stage;
                const done = i < stage;
                return (
                  <motion.div
                    key={s.id}
                    animate={{
                      borderColor: active ? "rgba(13,148,136,0.45)" : "rgba(226,232,240,1)",
                      backgroundColor: active ? "rgba(13,148,136,0.06)" : "rgba(248,250,252,1)",
                    }}
                    className="flex items-center justify-between rounded-xl border px-4 py-3"
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-mono ${
                          done || active ? "bg-accent text-white" : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {done ? "✓" : i + 1}
                      </span>
                      <div>
                        <p className="text-sm text-slate-900">{s.label}</p>
                        <AnimatePresence mode="wait">
                          {active ? (
                            <motion.p
                              key={s.detail}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              className="text-xs text-slate-700"
                            >
                              {s.detail}
                            </motion.p>
                          ) : null}
                        </AnimatePresence>
                      </div>
                    </div>
                    {active ? (
                      <span className="font-mono text-[10px] uppercase tracking-wider text-accent">live</span>
                    ) : null}
                  </motion.div>
                );
              })}
            </div>
          </div>

          <div className="flex flex-col gap-4">
            <div className="flex-1 rounded-3xl border border-slate-200 bg-white p-5 backdrop-blur-xl md:p-6">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700">Output preview</p>
              <pre className="mt-4 overflow-auto font-mono text-xs leading-relaxed text-accent-ice/90 md:text-sm">
                {SAMPLE_JSON}
              </pre>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {["Intelligence", "Network", "AI Graph"].map((label, i) => (
                <motion.div
                  key={label}
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2.4, repeat: Infinity, delay: i * 0.4 }}
                  className="rounded-2xl border border-slate-200 bg-white px-3 py-4 text-center"
                >
                  <p className="font-mono text-[10px] text-accent">{label}</p>
                  <p className="mt-1 text-xs text-slate-700">updating</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
