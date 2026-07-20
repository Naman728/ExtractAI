"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { api } from "@/lib/api";
import { ensureGuestKey, setGuestKey } from "@/lib/guest";

type Confident<T> = { value: T; confidence: number; evidence: string[] };

type AnalyzeResponse = {
  id: string;
  profile: {
    url: string;
    final_url: string;
    framework: Confident<string | null>;
    cms: Confident<string | null>;
    rendering_mode: Confident<string>;
    javascript_required: Confident<boolean>;
    cloudflare: Confident<boolean>;
    captcha: Confident<boolean>;
    robots: Confident<Record<string, unknown>>;
    sitemap_urls: Confident<string[]>;
    rss_urls: Confident<string[]>;
    open_graph: Confident<Record<string, string>>;
    twitter_cards: Confident<Record<string, string>>;
    response_time_ms: Confident<number>;
    estimated_page_size_bytes: Confident<number>;
    overall_confidence: number;
    estimated_complexity: Confident<number>;
    language: Confident<string | null>;
    status_code: Confident<number>;
    title: Confident<string | null>;
  };
  report: {
    website_type: string;
    framework: string | null;
    cms: string | null;
    strategy_recommendation: string;
    javascript_required: boolean;
    cloudflare: boolean;
    captcha: boolean;
    complexity_score: number;
    suggested_fetch_strategy: string;
    suggested_extractor: string;
    warnings: string[];
    potential_issues: string[];
    confidence: number;
  };
};

function Card({
  title,
  children,
  delay = 0,
}: {
  title: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35 }}
      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-lg shadow-slate-200/60"
    >
      <h3 className="mb-3 font-mono text-xs uppercase tracking-[0.18em] text-accent">{title}</h3>
      {children}
    </motion.div>
  );
}

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <p className="text-xs text-slate-700">{label}</p>
      <p className="mt-1 font-display text-xl text-slate-900">{value}</p>
      {sub ? <p className="mt-1 text-xs text-slate-700">{sub}</p> : null}
    </div>
  );
}

export default function IntelligencePage() {
  const [url, setUrl] = useState("https://example.com");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyzeResponse | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setData(null);
    try {
      const guestKey = ensureGuestKey();
      const { data: result, headers } = await api.post<AnalyzeResponse>(
        "/api/v1/intelligence/analyze",
        { url },
        guestKey,
      );
      const returned = headers.get("X-Guest-Key");
      if (returned) setGuestKey(returned);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const p = data?.profile;
  const r = data?.report;

  return (
    <main className="relative mx-auto min-h-screen max-w-6xl px-6 py-10">
      <div className="pointer-events-none absolute inset-0 bg-grid bg-[size:40px_40px] opacity-30" aria-hidden />
      <div className="relative z-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link href="/" className="font-display text-xl text-slate-900">
              Extract<span className="text-accent">AI</span>
            </Link>
            <h1 className="mt-3 font-display text-3xl text-slate-900 md:text-4xl">Website Intelligence</h1>
            <p className="mt-2 max-w-xl text-slate-600">
              Profile any URL before extraction — frameworks, CMS, robots, feeds, and a strategy
              recommendation. No content scraping.
            </p>
          </div>
          <Link href="/" className="text-sm text-accent hover:underline">
            ← Home
          </Link>
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
            className="min-w-0 flex-1 rounded-xl border border-transparent bg-slate-50 px-4 py-3 font-mono text-sm outline-none ring-accent/30 focus:ring-2"
            placeholder="https://example.com"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-accent px-6 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            {loading ? "Analyzing…" : "Analyze site"}
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-signal">{error}</p> : null}

        {r && p ? (
          <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card title="Strategy recommendation" delay={0.05}>
              <p className="text-sm leading-relaxed text-slate-200">{r.strategy_recommendation}</p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Metric label="Fetch strategy" value={r.suggested_fetch_strategy.replace(/_/g, " ")} />
                <Metric label="Extractor" value={r.suggested_extractor} />
              </div>
            </Card>

            <Card title="Stack" delay={0.1}>
              <div className="grid grid-cols-2 gap-3">
                <Metric
                  label="Framework"
                  value={p.framework.value ?? "—"}
                  sub={`${Math.round(p.framework.confidence * 100)}% conf`}
                />
                <Metric
                  label="CMS"
                  value={p.cms.value ?? "—"}
                  sub={`${Math.round(p.cms.confidence * 100)}% conf`}
                />
                <Metric label="Website type" value={r.website_type.replace(/_/g, " ")} />
                <Metric label="Rendering" value={p.rendering_mode.value} />
              </div>
            </Card>

            <Card title="Confidence & complexity" delay={0.15}>
              <div className="grid grid-cols-2 gap-3">
                <Metric label="Overall confidence" value={`${Math.round(p.overall_confidence * 100)}%`} />
                <Metric label="Complexity" value={`${Math.round(p.estimated_complexity.value)}`} />
                <Metric label="JS required" value={p.javascript_required.value ? "Yes" : "No"} />
                <Metric label="Status" value={String(p.status_code.value)} />
              </div>
            </Card>

            <Card title="Protection" delay={0.2}>
              <div className="grid grid-cols-2 gap-3">
                <Metric label="Cloudflare" value={p.cloudflare.value ? "Detected" : "No"} />
                <Metric label="CAPTCHA" value={p.captcha.value ? "Detected" : "No"} />
              </div>
              {r.warnings.length ? (
                <ul className="mt-4 space-y-1 text-sm text-signal">
                  {r.warnings.map((w) => (
                    <li key={w}>• {w}</li>
                  ))}
                </ul>
              ) : (
                <p className="mt-4 text-sm text-slate-700">No major warnings.</p>
              )}
            </Card>

            <Card title="Robots & discovery" delay={0.25}>
              <div className="grid grid-cols-2 gap-3">
                <Metric
                  label="robots.txt"
                  value={(p.robots.value as { available?: boolean })?.available ? "Found" : "Missing"}
                />
                <Metric label="Sitemaps" value={String(p.sitemap_urls.value.length)} />
                <Metric label="RSS feeds" value={String(p.rss_urls.value.length)} />
                <Metric label="Language" value={p.language.value ?? "—"} />
              </div>
            </Card>

            <Card title="Performance" delay={0.3}>
              <div className="grid grid-cols-2 gap-3">
                <Metric label="Response time" value={`${Math.round(p.response_time_ms.value)} ms`} />
                <Metric
                  label="Page size"
                  value={`${Math.round(p.estimated_page_size_bytes.value / 1024)} KB`}
                />
              </div>
              {p.title.value ? (
                <p className="mt-4 truncate text-sm text-slate-600" title={p.title.value}>
                  Title: {p.title.value}
                </p>
              ) : null}
            </Card>

            <Card title="Metadata" delay={0.35}>
              <p className="text-sm text-slate-600">
                Open Graph keys:{" "}
                <span className="text-slate-200">
                  {Object.keys(p.open_graph.value).length || "none"}
                </span>
              </p>
              <p className="mt-2 text-sm text-slate-600">
                Twitter Card keys:{" "}
                <span className="text-slate-200">
                  {Object.keys(p.twitter_cards.value).length || "none"}
                </span>
              </p>
              <p className="mt-3 break-all font-mono text-xs text-slate-700">{p.final_url}</p>
            </Card>
          </div>
        ) : null}
      </div>
    </main>
  );
}
