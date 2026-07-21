"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState, type ReactNode } from "react";

import { SiteHeader } from "@/components/site-header";
import { ExportDownloadButtons } from "@/components/export-download-buttons";
import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import { getGuestKey } from "@/lib/guest";

type KnowledgeNode = {
  id: string;
  label: string;
  type: string;
  confidence?: number;
};

type KnowledgeEdge = {
  id: string;
  source: string;
  target: string;
  type: string;
  label?: string | null;
};

type AIUnderstanding = {
  summary?: string;
  category?: string;
  category_confidence?: number;
  business_profile?: {
    organization_name?: string | null;
    description?: string | null;
    industry?: string | null;
    main_products?: string[];
    main_services?: string[];
    target_audience?: string | null;
    value_proposition?: string | null;
  };
  entities?: {
    people?: { name: string; role?: string | null }[];
    organizations?: { name: string; org_type?: string | null }[];
    products?: { name: string; price?: string | null }[];
    services?: { name: string }[];
    departments?: string[];
    locations?: { name: string; address?: string | null }[];
    contacts?: { kind: string; value: string; label?: string | null }[];
    technologies?: { name: string; category?: string | null }[];
    tags?: string[];
  };
  knowledge_graph?: {
    nodes?: KnowledgeNode[];
    edges?: KnowledgeEdge[];
    root_id?: string | null;
  };
  semantic_tags?: string[];
  overall_confidence?: number;
  observability?: {
    provider?: string;
    model?: string | null;
    latency_ms?: number;
    total_tokens?: number;
    estimated_cost_usd?: number;
    prompt_version?: string;
    cache_hit?: boolean;
    error?: string | null;
  };
  status?: string;
};

type Results = {
  job_id: string;
  url: string;
  status: string;
  strategy_used: string | null;
  schema_version: number;
  summary: Record<string, unknown>;
  normalized: Record<string, unknown>;
  ready?: {
    source?: Record<string, unknown>;
    summary?: string;
    category?: string;
    business_profile?: Record<string, unknown>;
    entities?: Record<string, Record<string, unknown>[]>;
    media?: Record<string, unknown>;
    links?: Record<string, unknown>[];
    contacts?: Record<string, unknown>;
    counts?: Record<string, number>;
  } | null;
  validation_report: Record<string, unknown>;
  section_confidence: Record<string, number>;
  duration_ms: number | null;
  overall_confidence: number | null;
  ai_status?: string | null;
  ai_understanding?: AIUnderstanding | null;
};

const SECTIONS: { key: string; label: string }[] = [
  { key: "officials", label: "Officials" },
  { key: "agent", label: "Browser Agent" },
  { key: "title", label: "Title" },
  { key: "products", label: "Products" },
  { key: "images", label: "Images" },
  { key: "meta", label: "Metadata" },
  { key: "headings", label: "Headings" },
  { key: "paragraphs", label: "Paragraphs" },
  { key: "links", label: "Links" },
  { key: "tables", label: "Tables" },
  { key: "prices", label: "Prices" },
  { key: "emails", label: "Emails" },
  { key: "phones", label: "Phones" },
  { key: "forms", label: "Forms" },
  { key: "buttons", label: "Buttons" },
  { key: "downloads", label: "Downloads" },
  { key: "social_links", label: "Social Links" },
  { key: "lists", label: "Lists" },
  { key: "json_ld", label: "JSON-LD" },
  { key: "open_graph", label: "Open Graph" },
  { key: "twitter", label: "Twitter" },
  { key: "canonical_url", label: "Canonical" },
  { key: "language", label: "Language" },
  { key: "favicon", label: "Favicon" },
];

function countOf(value: unknown): number {
  if (Array.isArray(value)) return value.length;
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    if (typeof obj.total === "number") return obj.total;
    return Object.keys(obj).length;
  }
  if (value) return 1;
  return 0;
}

function previewLines(value: unknown, max = 6): string[] {
  if (value == null) return [];
  if (typeof value === "string") return [value];
  if (typeof value === "number" || typeof value === "boolean") return [String(value)];
  if (Array.isArray(value)) {
    return value.slice(0, max).map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") {
        const o = item as Record<string, unknown>;
        return String(o.name || o.title || o.text || o.url || o.href || JSON.stringify(item).slice(0, 120));
      }
      return String(item);
    });
  }
  if (typeof value === "object") {
    const o = value as Record<string, unknown>;
    if (typeof o.title === "string") return [o.title];
    if (typeof o.description === "string") return [o.description];
    return Object.entries(o)
      .slice(0, max)
      .map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v).slice(0, 80)}`);
  }
  return [String(value)];
}

type ExtractedImage = { url: string; alt?: string | null; width?: unknown; height?: unknown };

function asImages(value: unknown): ExtractedImage[] {
  if (!Array.isArray(value)) return [];
  const out: ExtractedImage[] = [];
  const seen = new Set<string>();
  for (const item of value) {
    if (!item || typeof item !== "object") continue;
    const o = item as Record<string, unknown>;
    const url = typeof o.url === "string" ? o.url : typeof o.src === "string" ? o.src : "";
    if (!url || seen.has(url)) continue;
    seen.add(url);
    out.push({
      url,
      alt: typeof o.alt === "string" ? o.alt : null,
      width: o.width,
      height: o.height,
    });
  }
  return out;
}

function ImageGallery({ images }: { images: ExtractedImage[] }) {
  const [broken, setBroken] = useState<Record<string, boolean>>({});
  const [limit, setLimit] = useState(24);
  const visible = images.slice(0, limit);
  const failed = Object.values(broken).filter(Boolean).length;

  if (!images.length) {
    return <p className="text-sm font-medium text-slate-600">No images extracted.</p>;
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-700">
        <span>{images.length} images extracted</span>
        {failed > 0 ? <span className="text-orange-700">· {failed} failed to load</span> : null}
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        {visible.map((img, i) => {
          const isBroken = broken[img.url];
          return (
            <a
              key={`${i}-${img.url}`}
              href={img.url}
              target="_blank"
              rel="noreferrer"
              className="group overflow-hidden rounded-xl border border-slate-200 bg-slate-50 shadow-sm transition hover:border-accent"
              title={img.alt || img.url}
            >
              <div className="relative aspect-square w-full bg-slate-100">
                {isBroken ? (
                  <div className="flex h-full flex-col items-center justify-center gap-1 px-2 text-center">
                    <span className="text-xs font-bold text-slate-600">Couldn’t load</span>
                    <span className="line-clamp-2 break-all font-mono text-[10px] text-slate-500">
                      {img.url}
                    </span>
                  </div>
                ) : (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={img.url}
                    alt={img.alt || "Extracted image"}
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    className="h-full w-full object-contain p-1 transition group-hover:scale-[1.02]"
                    onError={() => setBroken((b) => ({ ...b, [img.url]: true }))}
                  />
                )}
              </div>
              {img.alt ? (
                <p className="line-clamp-2 border-t border-slate-100 px-2 py-1.5 text-[11px] font-medium text-slate-700">
                  {img.alt}
                </p>
              ) : null}
            </a>
          );
        })}
      </div>
      {images.length > limit ? (
        <button
          type="button"
          onClick={() => setLimit((n) => n + 24)}
          className="mt-4 rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-800 hover:border-accent hover:text-accent"
        >
          Show more images ({images.length - limit} left)
        </button>
      ) : null}
    </div>
  );
}

function Pill({ children, tone = "teal" }: { children: ReactNode; tone?: "teal" | "slate" | "sky" }) {
  const styles =
    tone === "sky"
      ? "bg-sky-100 text-sky-900 ring-sky-200"
      : tone === "slate"
        ? "bg-slate-100 text-slate-800 ring-slate-200"
        : "bg-teal-100 text-teal-900 ring-teal-200";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ring-1 ${styles}`}>
      {children}
    </span>
  );
}

function DataPanel({
  label,
  value,
  confidence,
  defaultOpen = false,
  query,
}: {
  label: string;
  value: unknown;
  confidence?: number;
  defaultOpen?: boolean;
  query: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [showJson, setShowJson] = useState(false);
  const json = JSON.stringify(value, null, 2);
  const matches = !query || json.toLowerCase().includes(query.toLowerCase());
  const n = countOf(value);
  if (!matches || n === 0) return null;

  const isImages = label === "Images";
  const images = isImages ? asImages(value) : [];
  const lines = previewLines(value);

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
      {/* Header: toggle sits next to title — not pushed to far-right edge */}
      <div className="border-b border-slate-100 px-5 py-4">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-base font-bold leading-none text-slate-900 hover:border-accent hover:text-accent"
            title={open ? "Collapse" : "Expand"}
          >
            {open ? "−" : "+"}
          </button>
          <h3 className="text-base font-bold text-slate-900">{label}</h3>
          <Pill tone="slate">{n} items</Pill>
          {confidence != null ? <Pill tone="sky">{Math.round(confidence * 100)}% conf</Pill> : null}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="rounded-lg px-2 py-1 text-xs font-bold text-accent hover:underline"
          >
            {open ? "Collapse" : "Expand"}
          </button>
        </div>

        {/* Collapsed preview */}
        {!open && !isImages ? (
          <ul className="mt-3 space-y-1.5 pl-10">
            {lines.slice(0, 3).map((line, i) => (
              <li key={`${i}-${line}`} className="truncate text-sm font-medium text-slate-800">
                {line}
              </li>
            ))}
            {n > 3 ? (
              <li className="text-xs font-semibold text-slate-600">+{n - 3} more</li>
            ) : null}
          </ul>
        ) : null}

        {/* Images: always show gallery preview even when collapsed */}
        {isImages ? (
          <div className="mt-4">
            <ImageGallery images={open ? images : images.slice(0, 8)} />
            {!open && images.length > 8 ? (
              <button
                type="button"
                onClick={() => setOpen(true)}
                className="mt-3 text-xs font-bold text-accent hover:underline"
              >
                Show all {images.length} images
              </button>
            ) : null}
          </div>
        ) : null}
      </div>

      {open && !isImages ? (
        <div className="px-5 py-4">
          <div className="mb-3 flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 hover:border-accent hover:text-accent"
              onClick={() => navigator.clipboard.writeText(json)}
            >
              Copy JSON
            </button>
            <button
              type="button"
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 hover:border-accent hover:text-accent"
              onClick={() => setShowJson((v) => !v)}
            >
              {showJson ? "Hide JSON" : "Show JSON"}
            </button>
          </div>
          {label === "Products" && Array.isArray(value) ? (
            <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {(value as Record<string, unknown>[]).slice(0, 24).map((p, idx) => {
                const name = String(p.name || p.title || `Product ${idx + 1}`);
                const price = p.price != null ? String(p.price) : null;
                const img =
                  typeof p.image === "string"
                    ? p.image
                    : typeof (p.image as { url?: string } | undefined)?.url === "string"
                      ? (p.image as { url: string }).url
                      : null;
                return (
                  <div
                    key={`${name}-${idx}`}
                    className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50"
                  >
                    {img ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={img}
                        alt={name}
                        loading="lazy"
                        referrerPolicy="no-referrer"
                        className="h-36 w-full bg-white object-contain p-2"
                      />
                    ) : (
                      <div className="flex h-24 items-center justify-center bg-slate-100 text-xs font-semibold text-slate-500">
                        No image
                      </div>
                    )}
                    <div className="border-t border-slate-200 px-3 py-2">
                      <p className="line-clamp-2 text-sm font-bold text-slate-900">{name}</p>
                      {price ? (
                        <p className="mt-1 text-xs font-semibold text-teal-800">{price}</p>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : null}
          {showJson ? (
            <pre className="max-h-80 overflow-auto rounded-xl border border-slate-200 bg-slate-50 p-4 font-mono text-xs font-medium leading-relaxed text-slate-900">
              {json}
            </pre>
          ) : label !== "Products" ? (
            <ul className="space-y-2">
              {previewLines(value, 40).map((line, i) => (
                <li
                  key={`${i}-${line}`}
                  className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-900"
                >
                  {line}
                </li>
              ))}
              {n > 40 ? (
                <li className="text-xs font-semibold text-slate-600">+{n - 40} more in JSON</li>
              ) : null}
            </ul>
          ) : null}
        </div>
      ) : null}

      {open && isImages ? (
        <div className="border-t border-slate-100 px-5 py-3">
          <button
            type="button"
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 hover:border-accent hover:text-accent"
            onClick={() => navigator.clipboard.writeText(json)}
          >
            Copy image JSON
          </button>
        </div>
      ) : null}
    </article>
  );
}

function AIResults({
  ai,
  status,
}: {
  ai: AIUnderstanding | null | undefined;
  status: string | null | undefined;
}) {
  if (status === "pending" || status === "running") {
    return (
      <section className="rounded-2xl border border-teal-200 bg-teal-50 p-6">
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-teal-800">
          AI Insights
        </p>
        <p className="mt-2 text-base font-semibold text-slate-900">
          Understanding engine is {status}… building knowledge from extracted data.
        </p>
      </section>
    );
  }

  if (status === "skipped" || (!ai && !status)) return null;

  if (!ai || status === "failed") {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-accent">
          AI Insights
        </p>
        <p className="mt-2 text-base font-medium text-slate-800">
          {ai?.observability?.error || "AI understanding unavailable for this job."}
        </p>
      </section>
    );
  }

  const entities = ai.entities || {};
  const profile = ai.business_profile || {};
  const graph = ai.knowledge_graph || {};
  const obs = ai.observability || {};
  const entityCount =
    (entities.people || []).length +
    (entities.organizations || []).length +
    (entities.products || []).length +
    (entities.services || []).length;

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-accent">
            AI Insights
          </p>
          <h2 className="mt-1 font-display text-2xl text-slate-900">What we understood</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {obs.provider ? <Pill tone="slate">{obs.provider}</Pill> : null}
          {obs.cache_hit ? <Pill>cache hit</Pill> : null}
          {obs.latency_ms != null ? <Pill tone="slate">{obs.latency_ms} ms</Pill> : null}
          {ai.overall_confidence != null ? (
            <Pill tone="sky">{Math.round(ai.overall_confidence * 100)}% conf</Pill>
          ) : null}
        </div>
      </div>

      {/* Always-visible hero summary — this is the “results arrived” moment */}
      <div className="rounded-2xl border border-teal-200 bg-gradient-to-br from-teal-50 via-white to-sky-50 p-6 shadow-card md:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-bold text-slate-900">Summary</p>
          {ai.category ? <Pill>{ai.category}</Pill> : null}
          {ai.category_confidence != null ? (
            <span className="text-xs font-semibold text-slate-700">
              type confidence {Math.round(ai.category_confidence * 100)}%
            </span>
          ) : null}
        </div>
        <p className="mt-4 text-lg font-medium leading-relaxed text-slate-900 md:text-xl">
          {ai.summary || "No summary generated."}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <h3 className="text-sm font-bold uppercase tracking-wide text-slate-900">Business profile</h3>
          <dl className="mt-4 space-y-3">
            {[
              ["Organization", profile.organization_name],
              ["Industry", profile.industry],
              ["Audience", profile.target_audience],
              ["Value", profile.value_proposition],
            ].map(([k, v]) => (
              <div key={k as string}>
                <dt className="text-xs font-bold uppercase tracking-wide text-slate-600">{k as string}</dt>
                <dd className="mt-0.5 text-sm font-semibold text-slate-900">{(v as string) || "—"}</dd>
              </div>
            ))}
            <div>
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-600">Description</dt>
              <dd className="mt-0.5 text-sm font-medium leading-relaxed text-slate-800">
                {profile.description || "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-600">Products</dt>
              <dd className="mt-0.5 text-sm font-medium text-slate-800">
                {(profile.main_products || []).length
                  ? (profile.main_products || []).join(", ")
                  : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-600">Services</dt>
              <dd className="mt-0.5 text-sm font-medium text-slate-800">
                {(profile.main_services || []).length
                  ? (profile.main_services || []).join(", ")
                  : "—"}
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-bold uppercase tracking-wide text-slate-900">Entities</h3>
            <Pill tone="slate">{entityCount} found</Pill>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {[
              ["People", (entities.people || []).map((p) => `${p.name}${p.role ? ` — ${p.role}` : ""}`)],
              ["Organizations", (entities.organizations || []).map((o) => o.name)],
              ["Products", (entities.products || []).map((p) => (p.price ? `${p.name} (${p.price})` : p.name))],
              ["Services", (entities.services || []).map((s) => s.name)],
              ["Locations", (entities.locations || []).map((l) => l.address || l.name)],
              ["Contacts", (entities.contacts || []).map((c) => `${c.kind}: ${c.value}`)],
            ].map(([label, items]) => (
              <div key={label as string}>
                <p className="text-xs font-bold uppercase tracking-wide text-slate-600">
                  {label as string}
                </p>
                {(items as string[]).length ? (
                  <ul className="mt-1.5 space-y-1">
                    {(items as string[]).slice(0, 6).map((item, i) => (
                      <li key={`${i}-${item}`} className="text-sm font-medium text-slate-900">
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-1.5 text-sm font-medium text-slate-500">None detected</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <h3 className="text-sm font-bold uppercase tracking-wide text-slate-900">Technologies & tags</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            {(entities.technologies || []).length ? (
              (entities.technologies || []).map((t, i) => (
                <span
                  key={`${i}-${t.name}`}
                  className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-800"
                >
                  {t.name}
                  {t.category ? ` · ${t.category}` : ""}
                </span>
              ))
            ) : (
              <p className="text-sm font-medium text-slate-600">No technologies inferred</p>
            )}
          </div>
          {(ai.semantic_tags || []).length ? (
            <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
              {(ai.semantic_tags || []).map((tag, i) => (
                <span
                  key={`${i}-${tag}`}
                  className="rounded-md bg-teal-50 px-2.5 py-1 text-xs font-bold text-teal-900 ring-1 ring-teal-200"
                >
                  {tag}
                </span>
              ))}
            </div>
          ) : null}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-bold uppercase tracking-wide text-slate-900">Knowledge graph</h3>
            <Pill tone="slate">{(graph.nodes || []).length} nodes</Pill>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {(graph.nodes || []).slice(0, 20).map((n) => (
              <span
                key={n.id}
                className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-semibold text-slate-900"
                title={n.type}
              >
                <span className="font-bold text-accent">{n.type}</span>
                <span className="text-slate-400"> · </span>
                {n.label}
              </span>
            ))}
          </div>
          {(graph.edges || []).length ? (
            <ul className="mt-4 max-h-40 space-y-1.5 overflow-auto border-t border-slate-100 pt-3 font-mono text-xs font-medium text-slate-800">
              {(graph.edges || []).slice(0, 24).map((e) => (
                <li key={e.id}>
                  {e.source} —{e.label || e.type}→ {e.target}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm font-medium text-slate-600">No relationships</p>
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
        <h3 className="text-sm font-bold uppercase tracking-wide text-slate-900">
          Confidence & observability
        </h3>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          {[
            ["Overall confidence", ai.overall_confidence != null ? `${Math.round(ai.overall_confidence * 100)}%` : "—"],
            ["Provider", obs.provider || "—"],
            ["Model", obs.model || "—"],
            ["Latency", obs.latency_ms != null ? `${obs.latency_ms} ms` : "—"],
            ["Tokens", obs.total_tokens != null ? String(obs.total_tokens) : "—"],
            ["Est. cost", obs.estimated_cost_usd != null ? `$${obs.estimated_cost_usd.toFixed(5)}` : "—"],
            ["Prompt version", obs.prompt_version || "—"],
            ["Cache", obs.cache_hit ? "hit" : "miss"],
          ].map(([k, v]) => (
            <div key={k} className="rounded-xl bg-slate-50 px-3 py-3 ring-1 ring-slate-200">
              <dt className="text-[11px] font-bold uppercase tracking-wide text-slate-600">{k}</dt>
              <dd className="mt-1 text-sm font-bold text-slate-900">{v}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

type AnyRec = Record<string, unknown>;

const IMAGE_KEY = /(image|img|thumbnail|thumb|photo|picture|cover|logo|avatar)/i;

function isUrl(v: unknown): v is string {
  return typeof v === "string" && /^https?:\/\//i.test(v.trim());
}

/** Drop null / empty values so each record stays clean and copy-friendly. */
function cleanRecord(o: AnyRec): AnyRec {
  const out: AnyRec = {};
  for (const [k, v] of Object.entries(o)) {
    if (v == null) continue;
    if (typeof v === "string" && !v.trim()) continue;
    if (Array.isArray(v) && v.length === 0) continue;
    if (typeof v === "object" && !Array.isArray(v) && Object.keys(v as AnyRec).length === 0)
      continue;
    out[k] = v;
  }
  return out;
}

/**
 * Consolidate the flat, section-by-section payload into a single object where
 * every entity (official, product, book, …) is ONE self-contained dictionary.
 * Related media/links are best-effort attached to each entity by name match.
 */
function buildConsolidated(
  normalized: AnyRec,
  ai?: AIUnderstanding | null,
  url?: string,
): { object: AnyRec; groups: { key: string; label: string; records: AnyRec[] }[] } {
  const images = asImages(normalized.images);
  const links = (Array.isArray(normalized.links) ? normalized.links : []).filter(
    (l) => l && typeof l === "object",
  ) as AnyRec[];

  const enrich = (rec: AnyRec): AnyRec => {
    const name = String(rec.name || rec.title || "").trim();
    const merged: AnyRec = { ...rec };
    if (name) {
      const lname = name.toLowerCase();
      const relImgs = images
        .filter((im) => (im.alt || "").toLowerCase().includes(lname))
        .map((im) => im.url);
      const relLinks = links
        .filter((l) => String(l.text || "").toLowerCase().includes(lname))
        .map((l) => ({ url: l.url, text: l.text }));
      if (relImgs.length && merged.images == null) merged.images = relImgs;
      if (relLinks.length && merged.links == null) merged.links = relLinks;
    }
    return cleanRecord(merged);
  };

  const toRecords = (v: unknown): AnyRec[] =>
    (Array.isArray(v) ? v : [])
      .filter((x) => x && typeof x === "object" && !Array.isArray(x))
      .map((x) => enrich(x as AnyRec));

  const groups: { key: string; label: string; records: AnyRec[] }[] = [];
  const pushGroup = (key: string, label: string, records: AnyRec[]) => {
    if (records.length) groups.push({ key, label, records });
  };

  // Officials live under officials.all
  const off = normalized.officials as AnyRec | undefined;
  if (off && Array.isArray(off.all)) pushGroup("officials", "Officials", toRecords(off.all));

  // Generic object collections
  const objectCollections: [string, string][] = [
    ["products", "Products"],
    ["tables", "Tables"],
    ["forms", "Forms"],
    ["json_ld", "JSON-LD"],
    ["downloads", "Downloads"],
  ];
  for (const [key, label] of objectCollections) {
    pushGroup(key, label, toRecords(normalized[key]));
  }

  // AI-derived entities → each already a dict
  const aiEnt = ai?.entities;
  if (aiEnt) {
    pushGroup("people", "People (AI)", toRecords(aiEnt.people));
    pushGroup("organizations", "Organizations (AI)", toRecords(aiEnt.organizations));
    pushGroup("ai_products", "Products (AI)", toRecords(aiEnt.products));
    pushGroup("locations", "Locations (AI)", toRecords(aiEnt.locations));
    pushGroup("contacts_ai", "Contacts (AI)", toRecords(aiEnt.contacts));
  }

  const source = cleanRecord({
    url: url,
    title: normalized.title,
    language: normalized.language,
    canonical_url: normalized.canonical_url,
    favicon: normalized.favicon,
    description: (normalized.meta as AnyRec | undefined)?.description,
    keywords: (normalized.meta as AnyRec | undefined)?.keywords,
  });

  const entities: AnyRec = {};
  for (const g of groups) entities[g.key] = g.records;

  const object = cleanRecord({
    source,
    summary: ai?.summary,
    category: ai?.category,
    business_profile: ai?.business_profile ? cleanRecord(ai.business_profile as AnyRec) : undefined,
    entities,
    media: cleanRecord({
      images: images.map((im) => cleanRecord({ url: im.url, alt: im.alt })),
    }),
    links: links.map((l) => cleanRecord({ url: l.url, text: l.text })),
    contacts: cleanRecord({
      emails: normalized.emails,
      phones: normalized.phones,
      social_links: normalized.social_links,
    }),
  });

  return { object, groups };
}

function CopyButton({
  text,
  label = "Copy",
  className,
}: {
  text: string;
  label?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1400);
      }}
      className={
        className ||
        "rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 hover:border-accent hover:text-accent"
      }
    >
      {copied ? "Copied!" : label}
    </button>
  );
}

function RecordCard({ record, index }: { record: AnyRec; index: number }) {
  const title = String(record.name || record.title || record.office || `Item ${index + 1}`);
  const primaryImg =
    Object.entries(record).find(([k, v]) => IMAGE_KEY.test(k) && isUrl(v))?.[1] ??
    (Array.isArray(record.images) && isUrl((record.images as unknown[])[0])
      ? (record.images as string[])[0]
      : undefined);

  const entries = Object.entries(record).filter(([k]) => k !== "name" && k !== "title");

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="flex items-start gap-3 p-3">
        {isUrl(primaryImg) ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={primaryImg as string}
            alt={title}
            loading="lazy"
            referrerPolicy="no-referrer"
            className="h-16 w-16 shrink-0 rounded-lg border border-slate-100 bg-slate-50 object-contain"
          />
        ) : null}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="truncate text-sm font-bold text-slate-900">{title}</p>
            <CopyButton
              text={JSON.stringify(record, null, 2)}
              className="shrink-0 rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-[11px] font-bold text-slate-700 hover:border-accent hover:text-accent"
            />
          </div>
          <dl className="mt-1.5 space-y-0.5">
            {entries.map(([k, v]) => (
              <div key={k} className="flex gap-2 text-xs">
                <dt className="shrink-0 font-semibold text-slate-500">{k}</dt>
                <dd className="min-w-0 break-words font-medium text-slate-800">
                  {isUrl(v) ? (
                    <a
                      href={v as string}
                      target="_blank"
                      rel="noreferrer"
                      className="break-all text-accent hover:underline"
                    >
                      {v as string}
                    </a>
                  ) : typeof v === "string" || typeof v === "number" || typeof v === "boolean" ? (
                    String(v)
                  ) : (
                    <span className="break-all font-mono text-[11px] text-slate-700">
                      {JSON.stringify(v)}
                    </span>
                  )}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}

const ENTITY_LABELS: Record<string, string> = {
  officials: "Officials",
  products: "Products",
  books: "Books",
  people: "People",
  organizations: "Organizations",
  locations: "Locations",
  downloads: "Downloads",
  tables: "Tables",
  forms: "Forms",
  catalog_items: "Catalog items",
  ai_products: "Products (AI)",
  contacts_ai: "Contacts (AI)",
  json_ld: "JSON-LD",
};

function groupsFromReady(ready: AnyRec): { key: string; label: string; records: AnyRec[] }[] {
  const entities = (ready.entities || {}) as Record<string, unknown>;
  const groups: { key: string; label: string; records: AnyRec[] }[] = [];
  for (const [key, value] of Object.entries(entities)) {
    if (!Array.isArray(value) || !value.length) continue;
    const records = value.filter((x) => x && typeof x === "object") as AnyRec[];
    if (!records.length) continue;
    groups.push({
      key,
      label: ENTITY_LABELS[key] || key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      records,
    });
  }
  return groups;
}

function ReadyMadeExport({
  jobId,
  ready,
  normalized,
  ai,
  url,
}: {
  jobId: string;
  ready?: AnyRec | null;
  normalized: AnyRec;
  ai?: AIUnderstanding | null;
  url?: string;
}) {
  const [view, setView] = useState<"cards" | "json">("json");
  const { object, groups } = useMemo(() => {
    if (ready && typeof ready === "object" && Object.keys(ready).length) {
      const g = groupsFromReady(ready);
      if (g.length) return { object: ready, groups: g };
    }
    return buildConsolidated(normalized, ai, url);
  }, [ready, normalized, ai, url]);
  const fullJson = useMemo(() => JSON.stringify(object, null, 2), [object]);

  // Always show when we have anything useful (source / contacts / media count)
  const hasAnything =
    groups.length > 0 ||
    Boolean((object as AnyRec).source) ||
    Boolean((object as AnyRec).contacts) ||
    Boolean((object as AnyRec).summary);

  if (!hasAnything) return null;
  const totalRecords = groups.reduce((n, g) => n + g.records.length, 0);

  return (
    <section
      id="section-ready"
      className="scroll-mt-8 overflow-hidden rounded-2xl border border-accent/30 bg-white shadow-card"
    >
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 bg-accent-soft/40 px-5 py-4">
        <div className="min-w-0">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-accent">
            Ready-made export
          </p>
          <h2 className="mt-1 font-display text-2xl text-slate-900">Copy or download</h2>
          <p className="mt-1 text-sm font-medium text-slate-700">
            {totalRecords > 0
              ? `${totalRecords} records across ${groups.length} groups — each entity is one complete dictionary (name, price, image, links…).`
              : "Page source + contacts packaged as one JSON object ready to paste."}
          </p>
        </div>
        <div className="ml-auto flex flex-col items-end gap-2">
          <div className="flex flex-wrap items-center justify-end gap-2">
            <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 text-xs font-bold">
              <button
                type="button"
                onClick={() => setView("cards")}
                className={`rounded-md px-3 py-1.5 ${view === "cards" ? "bg-accent text-white" : "text-slate-700"}`}
              >
                Grouped
              </button>
              <button
                type="button"
                onClick={() => setView("json")}
                className={`rounded-md px-3 py-1.5 ${view === "json" ? "bg-accent text-white" : "text-slate-700"}`}
              >
                JSON
              </button>
            </div>
            <CopyButton
              text={fullJson}
              label="Copy ready JSON"
              className="rounded-lg bg-accent px-4 py-2 text-xs font-bold text-white hover:bg-accent-dim"
            />
          </div>
          <ExportDownloadButtons jobId={jobId} />
        </div>
      </div>

      {view === "json" ? (
        <pre className="max-h-[32rem] overflow-auto bg-slate-50 p-4 font-mono text-xs font-medium leading-relaxed text-slate-900">
          {fullJson}
        </pre>
      ) : groups.length ? (
        <div className="space-y-6 p-5">
          {groups.map((g) => (
            <div key={g.key}>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">{g.label}</h3>
                <Pill tone="slate">{g.records.length}</Pill>
                <CopyButton
                  text={JSON.stringify(g.records, null, 2)}
                  label={`Copy ${g.label}`}
                  className="ml-auto rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-bold text-slate-800 hover:border-accent hover:text-accent"
                />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {g.records.slice(0, 60).map((rec, i) => (
                  <RecordCard key={`${g.key}-${i}`} record={rec} index={i} />
                ))}
              </div>
              {g.records.length > 60 ? (
                <p className="mt-2 text-xs font-semibold text-slate-600">
                  Showing first 60 — use “Copy {g.label}” for all {g.records.length}.
                </p>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <div className="p-5">
          <p className="text-sm font-medium text-slate-700">
            No entity groups yet — use <strong>Copy ready JSON</strong> for source/contacts/media.
          </p>
        </div>
      )}
    </section>
  );
}

export default function ResultsPage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;
  const [query, setQuery] = useState("");
  const [showRaw, setShowRaw] = useState(false);

  const { data, error, isLoading } = useQuery({
    queryKey: ["results", jobId],
    queryFn: () =>
      api.get<Results>(`/api/v1/results/${jobId}`, getGuestKey(), getAccessToken()),
    refetchInterval: (q) => {
      if (q.state.error) return 2000;
      const aiStatus = q.state.data?.ai_status;
      if (aiStatus === "pending" || aiStatus === "running") return 2000;
      return false;
    },
    retry: 8,
  });

  const normalized = data?.normalized || {};
  const overview = useMemo(() => {
    return SECTIONS.map((s) => ({
      ...s,
      count: countOf(normalized[s.key]),
    })).filter((s) => s.count > 0);
  }, [normalized]);

  const pageTitle =
    typeof normalized.title === "string"
      ? normalized.title
      : typeof (normalized.meta as { title?: string } | undefined)?.title === "string"
        ? (normalized.meta as { title: string }).title
        : null;

  const totalFields = overview.reduce((sum, s) => sum + s.count, 0);

  return (
    <main className="min-h-screen bg-void">
      <SiteHeader />
      <div className="mx-auto max-w-6xl px-5 pb-20 pt-2 md:px-6">
        <div className="flex flex-wrap items-center gap-4 text-sm font-semibold">
          <Link href="/" className="text-accent hover:underline">
            ← New extraction
          </Link>
          <Link href="/dashboard" className="text-slate-800 hover:text-slate-950">
            Dashboard
          </Link>
          <Link href={`/jobs/${jobId}`} className="ml-auto text-slate-800 hover:text-slate-950">
            Job status
          </Link>
        </div>

        {isLoading ? (
          <p className="mt-10 text-base font-semibold text-slate-800">Loading results…</p>
        ) : null}
        {error ? (
          <p className="mt-10 text-base font-semibold text-signal">
            {(error as Error).message} — still processing? Check job status.
          </p>
        ) : null}

        {data ? (
          <>
            {/* Success banner — makes completion obvious */}
            <div className="mt-6 rounded-2xl border border-teal-200 bg-teal-50 px-5 py-4 md:px-6">
              <div className="flex flex-wrap items-center gap-3">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-accent text-sm font-bold text-white">
                  ✓
                </span>
                <div>
                  <p className="text-base font-bold text-slate-900">Extraction complete</p>
                  <p className="text-sm font-medium text-slate-700">
                    {totalFields} structured fields across {overview.length} sections
                    {data.ai_status === "completed" ? " · AI insights ready" : ""}
                  </p>
                </div>
                <button
                  type="button"
                  className="ml-auto rounded-lg border border-teal-300 bg-white px-3 py-1.5 text-xs font-bold text-teal-900 hover:bg-teal-50"
                  onClick={() =>
                    navigator.clipboard.writeText(
                      JSON.stringify(data.ready || data.normalized, null, 2),
                    )
                  }
                >
                  Copy ready JSON
                </button>
              </div>
            </div>

            <header className="mt-8">
              <p className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-accent">
                Results
              </p>
              <h1 className="mt-2 font-display text-3xl text-slate-900 md:text-4xl">
                {pageTitle || "Extracted page data"}
              </h1>
              <p className="mt-3 break-all font-mono text-sm font-semibold text-slate-800">
                {data.url}
              </p>
            </header>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["Strategy", data.strategy_used || "—"],
                ["Duration", data.duration_ms != null ? `${data.duration_ms} ms` : "—"],
                [
                  "Confidence",
                  data.overall_confidence != null
                    ? `${Math.round(data.overall_confidence * 100)}%`
                    : "—",
                ],
                ["Schema", `v${data.schema_version}`],
              ].map(([k, v]) => (
                <div
                  key={k}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-card"
                >
                  <p className="text-[11px] font-bold uppercase tracking-wide text-slate-600">{k}</p>
                  <p className="mt-1.5 font-display text-2xl font-semibold text-slate-900">{v}</p>
                </div>
              ))}
            </div>

            {/* Field inventory chips — always visible inventory of what came back */}
            <div className="mt-8">
              <h2 className="font-display text-xl text-slate-900">What was extracted</h2>
              <p className="mt-1 text-sm font-medium text-slate-700">
                Click a field to jump to its panel below.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <a
                  href="#section-ready"
                  className="rounded-full border border-accent/40 bg-accent-soft px-3.5 py-1.5 text-xs font-bold text-accent-dim shadow-sm hover:border-accent"
                >
                  Ready-made export ↓
                </a>
                {overview.map((s) => (
                  <a
                    key={s.key}
                    href={`#section-${s.key}`}
                    className="rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-bold text-slate-900 shadow-sm hover:border-accent hover:text-accent"
                  >
                    {s.label}
                    <span className="ml-1.5 text-slate-600">({s.count})</span>
                  </a>
                ))}
              </div>
            </div>

            <div className="mt-10">
              <ReadyMadeExport
                jobId={jobId}
                ready={data.ready as AnyRec | null | undefined}
                normalized={normalized}
                ai={data.ai_understanding}
                url={data.url}
              />
            </div>

            <div className="mt-10">
              <AIResults ai={data.ai_understanding} status={data.ai_status} />
            </div>

            <div className="mt-12">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="font-mono text-[11px] font-bold uppercase tracking-[0.16em] text-accent">
                    Structured data
                  </p>
                  <h2 className="mt-1 font-display text-2xl text-slate-900">Extracted fields</h2>
                </div>
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Filter sections…"
                  className="w-full max-w-xs rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-900 outline-none ring-accent/30 placeholder:text-slate-500 focus:ring-2"
                />
              </div>

              <div className="mt-5 grid gap-4">
                {SECTIONS.map((s) => (
                  <div key={s.key} id={`section-${s.key}`} className="scroll-mt-8">
                    <DataPanel
                      label={s.label}
                      value={normalized[s.key]}
                      confidence={data.section_confidence?.[s.key]}
                      defaultOpen={
                        s.key === "title" ||
                        s.key === "products" ||
                        s.key === "officials" ||
                        s.key === "images"
                      }
                      query={query}
                    />
                  </div>
                ))}
              </div>

              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => setShowRaw((v) => !v)}
                  className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-800 hover:border-accent hover:text-accent"
                >
                  {showRaw ? "Hide raw JSON" : "Show full raw JSON"}
                </button>
                {showRaw ? (
                  <pre className="mt-3 max-h-[28rem] overflow-auto rounded-2xl border border-slate-200 bg-slate-50 p-4 font-mono text-xs font-medium leading-relaxed text-slate-900">
                    {JSON.stringify(normalized, null, 2)}
                  </pre>
                ) : null}
              </div>
            </div>

            <p className="mt-10 text-sm font-medium text-slate-700">
              Exports (JSON / CSV / Excel) require a signed-in account that owns the job.
            </p>
          </>
        ) : null}
      </div>
    </main>
  );
}
