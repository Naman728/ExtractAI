"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { ensureGuestKey, setGuestKey } from "@/lib/guest";

type Endpoint = {
  url: string;
  method: string;
  endpoint_type: string;
  content_type: string | null;
  status_code: number | null;
  authentication_required: boolean;
  returns_json: boolean;
  estimated_value: number;
  confidence: number;
  framework_hint: string | null;
  source: string;
};

type Recommendation = {
  preferred_data_source: string;
  fallback_sources: string[];
  estimated_speed: string;
  estimated_reliability: number;
  reasoning: string[];
  top_endpoints: string[];
};

type NetworkResponse = {
  id: string;
  network_profile: {
    final_url: string;
    endpoints: Endpoint[];
    rest_endpoints: Endpoint[];
    graphql_endpoints: Endpoint[];
    json_feeds: Endpoint[];
    xml_feeds: Endpoint[];
    xhr_candidates: Endpoint[];
    nextjs_signals: string[];
    shopify_signals: string[];
    wordpress_signals: string[];
    websocket_detected: boolean;
    sse_detected: boolean;
    recommendation: Recommendation;
    timings: Record<string, number>;
    diagnostics: Record<string, unknown>;
  };
  execution_recommendation: Recommendation;
  metrics: Record<string, number | boolean>;
};

type IntelResponse = { id: string };
type StrategyResponse = { id: string; execution_plan: { preferred_data_source?: string } };

const FILTERS = [
  "all",
  "rest",
  "graphql",
  "json",
  "xhr",
  "fetch",
  "media",
  "assets",
] as const;

type Filter = (typeof FILTERS)[number];

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

function matchesFilter(ep: Endpoint, filter: Filter): boolean {
  if (filter === "all") return true;
  if (filter === "rest") return ep.endpoint_type === "rest" || ep.endpoint_type === "next_data";
  if (filter === "graphql") return ep.endpoint_type === "graphql";
  if (filter === "json") return ep.endpoint_type === "json_feed" || ep.returns_json;
  if (filter === "xhr") return ep.source === "playwright" && ep.endpoint_type !== "static_asset";
  if (filter === "fetch") return ep.source === "html_script" || ep.source === "playwright";
  if (filter === "media") return ep.endpoint_type === "media";
  if (filter === "assets") return ep.endpoint_type === "static_asset";
  return true;
}

export default function NetworkIntelligencePage() {
  const [url, setUrl] = useState("https://example.com");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<NetworkResponse | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const guestKey = ensureGuestKey();
      const { data: intel, headers } = await api.post<IntelResponse>(
        "/api/v1/intelligence/analyze",
        { url },
        guestKey,
      );
      const returned = headers.get("X-Guest-Key");
      if (returned) setGuestKey(returned);
      const key = returned || guestKey;

      const { data: strategy } = await api.post<StrategyResponse>(
        "/api/v1/strategy/analyze",
        { website_profile_id: intel.id },
        key,
      );

      const { data: network } = await api.post<NetworkResponse>(
        "/api/v1/network/analyze",
        {
          website_profile_id: intel.id,
          strategy_analysis_id: strategy.id,
        },
        key,
      );
      setResult(network);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const endpoints = useMemo(() => {
    if (!result) return [];
    return result.network_profile.endpoints.filter((ep) => matchesFilter(ep, filter));
  }, [result, filter]);

  const rec = result?.execution_recommendation;

  return (
    <main className="relative mx-auto min-h-screen max-w-6xl px-6 py-10">
      <div className="pointer-events-none absolute inset-0 bg-grid bg-[size:40px_40px] opacity-30" />
      <div className="relative z-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link href="/" className="font-display text-xl text-slate-900">
              Extract<span className="text-accent">AI</span>
            </Link>
            <h1 className="mt-3 font-display text-3xl text-slate-900 md:text-4xl">
              Network Intelligence
            </h1>
            <p className="mt-2 max-w-2xl text-slate-600">
              Discover public REST, GraphQL, JSON feeds, and XHR sources — classify and rank them
              without extracting via APIs.
            </p>
          </div>
          <div className="flex gap-4 text-sm">
            <Link href="/intelligence" className="text-slate-600 hover:text-slate-950">
              Intelligence
            </Link>
            <Link href="/strategy" className="text-slate-600 hover:text-slate-950">
              Strategy
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
            {loading ? "Discovering…" : "Analyze network"}
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-signal">{error}</p> : null}

        {result && rec ? (
          <div className="mt-10 space-y-4">
            <div className="grid gap-4 lg:grid-cols-3">
              <Panel title="Suggested data source" delay={0.05}>
                <p className="font-display text-2xl text-slate-900">
                  {rec.preferred_data_source.replace(/_/g, " ")}
                </p>
                <p className="mt-2 text-sm text-slate-600">
                  Speed {rec.estimated_speed} · reliability{" "}
                  {Math.round(rec.estimated_reliability * 100)}%
                </p>
                <p className="mt-3 text-xs text-slate-700">
                  Pipeline still extracts via HTML until API extraction ships.
                </p>
              </Panel>
              <Panel title="Fallback sources" delay={0.1}>
                <ul className="space-y-2 text-sm text-slate-700">
                  {rec.fallback_sources.map((s) => (
                    <li key={s} className="font-mono text-xs">
                      {s}
                    </li>
                  ))}
                </ul>
              </Panel>
              <Panel title="Discovery metrics" delay={0.15}>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="text-slate-700">Endpoints</dt>
                    <dd className="text-slate-900">{String(result.metrics.endpoints_found ?? 0)}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-700">Useful</dt>
                    <dd className="text-slate-900">{String(result.metrics.useful_endpoints ?? 0)}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-700">Discovery</dt>
                    <dd className="font-mono text-xs text-slate-900">
                      {Math.round(Number(result.metrics.discovery_time_ms ?? 0))} ms
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-700">Classify</dt>
                    <dd className="font-mono text-xs text-slate-900">
                      {Math.round(Number(result.metrics.classification_time_ms ?? 0))} ms
                    </dd>
                  </div>
                </dl>
              </Panel>
            </div>

            <Panel title="Framework signals" delay={0.18}>
              <div className="flex flex-wrap gap-2 text-xs">
                {result.network_profile.nextjs_signals.map((s) => (
                  <span key={`n-${s}`} className="rounded-md border border-slate-200 px-2 py-1 text-slate-700">
                    Next.js · {s}
                  </span>
                ))}
                {result.network_profile.shopify_signals.map((s) => (
                  <span key={`s-${s}`} className="rounded-md border border-slate-200 px-2 py-1 text-slate-700">
                    Shopify · {s}
                  </span>
                ))}
                {result.network_profile.wordpress_signals.map((s) => (
                  <span key={`w-${s}`} className="rounded-md border border-slate-200 px-2 py-1 text-slate-700">
                    WordPress · {s}
                  </span>
                ))}
                {result.network_profile.websocket_detected ? (
                  <span className="rounded-md border border-slate-200 px-2 py-1 text-slate-700">
                    WebSocket
                  </span>
                ) : null}
                {result.network_profile.sse_detected ? (
                  <span className="rounded-md border border-slate-200 px-2 py-1 text-slate-700">SSE</span>
                ) : null}
                {!result.network_profile.nextjs_signals.length &&
                !result.network_profile.shopify_signals.length &&
                !result.network_profile.wordpress_signals.length ? (
                  <span className="text-slate-700">No CMS/framework API signals detected.</span>
                ) : null}
              </div>
            </Panel>

            <Panel title="Detected endpoints" delay={0.2}>
              <div className="mb-4 flex flex-wrap gap-2">
                {FILTERS.map((f) => (
                  <button
                    key={f}
                    type="button"
                    onClick={() => setFilter(f)}
                    className={`rounded-md px-3 py-1.5 font-mono text-xs uppercase tracking-wide ${
                      filter === f
                        ? "bg-accent text-white"
                        : "border border-slate-200 text-slate-600 hover:text-slate-950"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] text-left text-sm">
                  <thead className="font-mono text-xs uppercase tracking-wider text-slate-700">
                    <tr>
                      <th className="pb-3 pr-3">Type</th>
                      <th className="pb-3 pr-3">Method</th>
                      <th className="pb-3 pr-3">Status</th>
                      <th className="pb-3 pr-3">URL</th>
                      <th className="pb-3 pr-3">Usefulness</th>
                      <th className="pb-3 pr-3">Confidence</th>
                      <th className="pb-3">Auth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {endpoints.map((ep) => (
                      <tr key={`${ep.method}:${ep.url}`} className="border-t border-slate-100">
                        <td className="py-3 pr-3 font-mono text-xs text-accent">{ep.endpoint_type}</td>
                        <td className="py-3 pr-3 font-mono text-xs text-slate-900">{ep.method}</td>
                        <td className="py-3 pr-3 font-mono text-xs text-slate-700">
                          {ep.status_code ?? "—"}
                        </td>
                        <td className="max-w-xs truncate py-3 pr-3 font-mono text-xs text-slate-700">
                          {ep.url}
                        </td>
                        <td className="py-3 pr-3 text-slate-900">{Math.round(ep.estimated_value)}</td>
                        <td className="py-3 pr-3 text-slate-700">
                          {Math.round(ep.confidence * 100)}%
                        </td>
                        <td className="py-3 text-slate-600">
                          {ep.authentication_required ? "Required" : "Public"}
                        </td>
                      </tr>
                    ))}
                    {!endpoints.length ? (
                      <tr>
                        <td colSpan={7} className="py-6 text-center text-slate-700">
                          No endpoints match this filter.
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </Panel>

            <Panel title="Pipeline recommendation" delay={0.25}>
              <ul className="space-y-2 text-sm text-slate-700">
                {rec.reasoning.map((line) => (
                  <li key={line}>• {line}</li>
                ))}
              </ul>
              {rec.top_endpoints.length ? (
                <div className="mt-4">
                  <p className="mb-2 font-mono text-xs uppercase tracking-wider text-slate-700">
                    Top endpoints
                  </p>
                  <ul className="space-y-1 font-mono text-xs text-slate-600">
                    {rec.top_endpoints.map((u) => (
                      <li key={u} className="truncate">
                        {u}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Panel>
          </div>
        ) : null}
      </div>
    </main>
  );
}
