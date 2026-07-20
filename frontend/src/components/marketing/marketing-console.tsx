"use client";

import { AnalyzeForm } from "@/components/landing/analyze-form";

/** Real extraction console — same working form as the current homepage. */
export function MarketingConsole() {
  return (
    <section id="console" className="scroll-mt-28 px-5 py-16 md:px-6 md:py-24">
      <div className="mx-auto max-w-2xl text-center">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-accent">Try it now</p>
        <h2 className="mt-3 font-display text-3xl text-slate-900 md:text-4xl">Start a real extraction</h2>
        <p className="mt-3 text-sm text-slate-600">
          This is the live ExtractAI console — not a mock. Paste a public URL to run the full pipeline.
        </p>
        <div className="mt-8 text-left">
          <AnalyzeForm />
        </div>
      </div>
    </section>
  );
}
