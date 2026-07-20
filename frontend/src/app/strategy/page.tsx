"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { api } from "@/lib/api";
import { ensureGuestKey, setGuestKey } from "@/lib/guest";

type StrategyScore = {
  strategy_id: string;
  strategy_name: string;
  suitability_score: number;
  confidence: number;
  estimated_runtime_ms: number;
  estimated_cost: number;
  reason: string;
  warnings: string[];
  advantages: string[];
  disadvantages: string[];
  can_handle: boolean;
  reject_reason: string | null;
};

type ExecutionPlan = {
  strategy: string;
  strategy_id: string;
  fetch_engine: string;
  cleaner: string;
  extractor: string;
  normalizer: string;
  validator: string;
  storage: string;
  estimated_duration_ms: number;
  complexity: number;
  confidence: number;
  warnings: string[];
  fallback_strategy: string | null;
  future_alternatives: string[];
  pipeline_stages: string[];
};

type StrategyResponse = {
  id: string;
  website_profile_id: string;
  execution_plan: ExecutionPlan;
  ranking: {
    scores: StrategyScore[];
    chosen_strategy_id: string;
    chosen_strategy_name: string;
    decision_time_ms: number;
  };
  reasoning: string[];
  warnings: string[];
  confidence: number;
};

type IntelResponse = {
  id: string;
  report: {
    suggested_fetch_strategy: string;
    website_type: string;
    framework: string | null;
    cms: string | null;
  };
  profile: {
    title: { value: string | null };
    framework: { value: string | null };
    cms: { value: string | null };
    javascript_required: { value: boolean };
    cloudflare: { value: boolean };
    overall_confidence: number;
  };
};

function Panel({
  title,
  children,
  delay = 0,
}: {
  title: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35 }}
      className="rounded-2xl border border-slate-200 bg-white p-5"
    >
      <h2 className="mb-4 font-mono text-xs uppercase tracking-[0.18em] text-accent">{title}</h2>
      {children}
    </motion.section>
  );
}

function ScoreBar({ score, active }: { score: number; active?: boolean }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-50">
      <div
        className={`h-full rounded-full ${active ? "bg-accent" : "bg-slate-500"}`}
        style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
      />
    </div>
  );
}

export default function StrategyViewerPage() {
  const [url, setUrl] = useState("https://example.com");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [intel, setIntel] = useState<IntelResponse | null>(null);
  const [strategy, setStrategy] = useState<StrategyResponse | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setIntel(null);
    setStrategy(null);
    try {
      const guestKey = ensureGuestKey();
      const { data: profileResult, headers } = await api.post<IntelResponse>(
        "/api/v1/intelligence/analyze",
        { url },
        guestKey,
      );
      const returned = headers.get("X-Guest-Key");
      if (returned) setGuestKey(returned);
      setIntel(profileResult);

      const { data: strategyResult } = await api.post<StrategyResponse>(
        "/api/v1/strategy/analyze",
        { website_profile_id: profileResult.id },
        returned || guestKey,
      );
      setStrategy(strategyResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Strategy analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const plan = strategy?.execution_plan;
  const chosenId = strategy?.ranking.chosen_strategy_id;

  return (
    <main className="relative mx-auto min-h-screen max-w-6xl px-6 py-10">
      <div className="pointer-events-none absolute inset-0 bg-grid bg-[size:40px_40px] opacity-30" />
      <div className="relative z-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link href="/" className="font-display text-xl text-slate-900">
              Extract<span className="text-accent">AI</span>
            </Link>
            <h1 className="mt-3 font-display text-3xl text-slate-900 md:text-4xl">Strategy Viewer</h1>
            <p className="mt-2 max-w-2xl text-slate-600">
              Profile a site, score candidate strategies, and preview the execution plan — without
              extracting content.
            </p>
          </div>
          <div className="flex gap-4 text-sm">
            <Link href="/intelligence" className="text-slate-600 hover:text-slate-950">
              Intelligence
            </Link>
            <Link href="/network" className="text-slate-600 hover:text-slate-950">
              Network
            </Link>
            <Link href="/" className="text-accent hover:underline">
              Home
            </Link>
          </div>
        </div>

        <form
          onSubmit={onSubmit}
          className="mt-8 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-3 md:flex-row"
        >
          <input
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="min-w-0 flex-1 rounded-xl bg-slate-50 px-4 py-3 font-mono text-sm outline-none ring-accent/30 focus:ring-2"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-accent px-6 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            {loading ? "Deciding…" : "Run strategy"}
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-signal">{error}</p> : null}

        {intel && strategy && plan ? (
          <div className="mt-10 space-y-4">
            <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
              <span className="rounded-md border border-slate-200 px-2 py-1 text-slate-900">Profile</span>
              <span>→</span>
              <span className="rounded-md border border-slate-200 px-2 py-1 text-slate-900">Candidates</span>
              <span>→</span>
              <span className="rounded-md border border-accent/40 bg-accent/10 px-2 py-1 text-accent">
                {strategy.ranking.chosen_strategy_name}
              </span>
              <span>→</span>
              <span className="rounded-md border border-slate-200 px-2 py-1 text-slate-900">Execution plan</span>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <Panel title="Website profile" delay={0.05}>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="text-slate-700">Title</dt>
                    <dd className="text-slate-900">{intel.profile.title.value ?? "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-700">Type</dt>
                    <dd className="text-slate-900">{intel.report.website_type}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-700">Framework</dt>
                    <dd className="text-slate-900">{intel.profile.framework.value ?? "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-700">CMS</dt>
                    <dd className="text-slate-900">{intel.profile.cms.value ?? "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-700">JS required</dt>
                    <dd className="text-slate-900">{intel.profile.javascript_required.value ? "Yes" : "No"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-700">Cloudflare</dt>
                    <dd className="text-slate-900">{intel.profile.cloudflare.value ? "Yes" : "No"}</dd>
                  </div>
                </dl>
              </Panel>

              <Panel title="Chosen strategy" delay={0.1}>
                <p className="font-display text-2xl text-slate-900">{strategy.ranking.chosen_strategy_name}</p>
                <p className="mt-2 text-sm text-slate-600">
                  Decision in {strategy.ranking.decision_time_ms} ms · confidence{" "}
                  {Math.round(strategy.confidence * 100)}%
                </p>
                <p className="mt-4 text-sm text-slate-700">
                  Fallback: {plan.fallback_strategy ?? "none"}
                </p>
              </Panel>
            </div>

            <Panel title="Candidate strategies & scores" delay={0.15}>
              <div className="space-y-4">
                {strategy.ranking.scores.map((s) => (
                  <div
                    key={s.strategy_id}
                    className={`rounded-xl border p-4 ${
                      s.strategy_id === chosenId
                        ? "border-accent/50 bg-accent/5"
                        : "border-slate-200 bg-slate-50/50"
                    }`}
                  >
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="font-medium text-slate-900">
                          {s.strategy_name}
                          {s.strategy_id === chosenId ? (
                            <span className="ml-2 text-xs text-accent">chosen</span>
                          ) : null}
                          {!s.can_handle ? (
                            <span className="ml-2 text-xs text-signal">skipped</span>
                          ) : null}
                        </p>
                        <p className="text-xs text-slate-700">{s.reason}</p>
                      </div>
                      <p className="font-mono text-sm text-slate-900">
                        {s.suitability_score.toFixed(1)}
                      </p>
                    </div>
                    <ScoreBar score={s.suitability_score} active={s.strategy_id === chosenId} />
                    <div className="mt-3 grid gap-2 text-xs text-slate-600 md:grid-cols-3">
                      <p>Conf {Math.round(s.confidence * 100)}%</p>
                      <p>~{s.estimated_runtime_ms} ms</p>
                      <p>Cost {s.estimated_cost}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <div className="grid gap-4 lg:grid-cols-2">
              <Panel title="Execution plan" delay={0.2}>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  {[
                    ["Fetch", plan.fetch_engine],
                    ["Cleaner", plan.cleaner],
                    ["Extractor", plan.extractor],
                    ["Normalizer", plan.normalizer],
                    ["Validator", plan.validator],
                    ["Storage", plan.storage],
                    ["Duration", `${plan.estimated_duration_ms} ms`],
                    ["Complexity", String(Math.round(plan.complexity))],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-slate-700">{k}</dt>
                      <dd className="font-mono text-xs text-slate-900 md:text-sm">{v}</dd>
                    </div>
                  ))}
                </dl>
              </Panel>

              <Panel title="Pipeline preview" delay={0.25}>
                <ol className="space-y-2">
                  {plan.pipeline_stages.map((stage, i) => (
                    <li key={stage} className="flex items-center gap-3 text-sm">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 font-mono text-xs text-accent">
                        {i + 1}
                      </span>
                      <span className="text-slate-200">{stage.replace(/_/g, " ")}</span>
                    </li>
                  ))}
                </ol>
                {plan.future_alternatives?.length ? (
                  <p className="mt-4 text-xs text-slate-700">
                    Future alternatives: {plan.future_alternatives.join(", ")}
                  </p>
                ) : null}
              </Panel>
            </div>

            <Panel title="Warnings & reasoning" delay={0.3}>
              {strategy.warnings.length ? (
                <ul className="mb-4 space-y-1 text-sm text-signal">
                  {strategy.warnings.map((w) => (
                    <li key={w}>• {w}</li>
                  ))}
                </ul>
              ) : (
                <p className="mb-4 text-sm text-slate-700">No warnings.</p>
              )}
              <ul className="space-y-1 font-mono text-xs text-slate-600">
                {strategy.reasoning.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </Panel>
          </div>
        ) : null}
      </div>
    </main>
  );
}
