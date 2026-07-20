"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api } from "@/lib/api";
import { getValidAccessToken } from "@/lib/auth";
import { ensureGuestKey, setGuestKey } from "@/lib/guest";

/**
 * Parse the agent inputs box into either:
 *  - addresses[] for BallotReady-style batch
 *  - inputs{} for the general browser agent (query / topics / address / key=value)
 */
function parseAgentPayload(raw: string, url: string): {
  addresses: string[];
  inputs: Record<string, string>;
  workflow?: string;
} {
  const trimmed = raw.trim();
  if (!trimmed) {
    return { addresses: [], inputs: {} };
  }

  const isBallotReady = url.toLowerCase().includes("ballotready");

  // JSON object: {"query":"FastAPI"} or {"address":"..."} or {"topics":[...]}
  if (trimmed.startsWith("{")) {
    try {
      const obj = JSON.parse(trimmed) as Record<string, unknown>;
      const inputs: Record<string, string> = {};
      for (const [k, v] of Object.entries(obj)) {
        if (v == null) continue;
        inputs[k] = typeof v === "string" ? v : JSON.stringify(v);
      }
      const workflow =
        isBallotReady && inputs.address ? "ballotready_officials" : undefined;
      return { addresses: [], inputs, workflow };
    } catch {
      // fall through
    }
  }

  // JSON array
  if (trimmed.startsWith("[")) {
    try {
      const arr = JSON.parse(trimmed) as unknown;
      if (Array.isArray(arr)) {
        const items = arr.map((v) => String(v).trim()).filter(Boolean);
        if (isBallotReady) {
          return {
            addresses: dedupe(items),
            inputs: {},
            workflow: "ballotready_officials",
          };
        }
        // Topic / search list → general browser agent
        return {
          addresses: [],
          inputs: {
            topics: JSON.stringify(items),
            query: items[0] || "",
          },
        };
      }
    } catch {
      // fall through
    }
  }

  // key=value lines
  if (/^\s*[\w.-]+\s*=/m.test(trimmed) && trimmed.includes("=")) {
    const inputs: Record<string, string> = {};
    for (const line of trimmed.split(/\r?\n/)) {
      const m = line.match(/^\s*([\w.-]+)\s*=\s*(.+)\s*$/);
      if (m) inputs[m[1].toLowerCase()] = m[2].trim();
    }
    if (Object.keys(inputs).length) {
      const workflow =
        isBallotReady && inputs.address ? "ballotready_officials" : undefined;
      return { addresses: [], inputs, workflow };
    }
  }

  // Multi-line: BallotReady → addresses; otherwise → topics list
  if (trimmed.includes("\n")) {
    const lines = dedupe(
      trimmed
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter(Boolean),
    );
    if (isBallotReady) {
      return {
        addresses: lines,
        inputs: lines.length === 1 ? { address: lines[0] } : {},
        workflow: "ballotready_officials",
      };
    }
    return {
      addresses: [],
      inputs: { topics: JSON.stringify(lines), query: lines[0] },
    };
  }

  // Single line
  if (isBallotReady) {
    return {
      addresses: [trimmed],
      inputs: { address: trimmed },
      workflow: "ballotready_officials",
    };
  }

  // Looks like a street address → send as address; else as query
  const looksLikeAddress = /\d/.test(trimmed) && /,/.test(trimmed);
  if (looksLikeAddress) {
    return { addresses: [], inputs: { address: trimmed } };
  }
  return { addresses: [], inputs: { query: trimmed } };
}

function dedupe(parts: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of parts) {
    const key = part.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(part);
  }
  return out;
}

function normalizeUrl(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return trimmed;
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}

export function AnalyzeForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [agentInput, setAgentInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const guestKey = ensureGuestKey();
      const token = await getValidAccessToken();
      const normalizedUrl = normalizeUrl(url);
      if (!normalizedUrl) {
        setError("Enter a website URL");
        return;
      }
      setUrl(normalizedUrl);
      const { addresses, inputs, workflow } = parseAgentPayload(agentInput, normalizedUrl);

      // Only BallotReady (or explicit multi-address) uses /batches.
      // Topic/search JSON arrays must stay on a single general-browser job.
      const isAddressBatch =
        addresses.length >= 2 &&
        (Boolean(workflow === "ballotready_officials") ||
          normalizedUrl.toLowerCase().includes("ballotready") ||
          addresses.every((a) => /\d/.test(a) && /,/.test(a)));

      if (isAddressBatch) {
        const { data, headers } = await api.post<{ id: string }>(
          "/api/v1/batches",
          { url: normalizedUrl, addresses, workflow },
          guestKey,
          token,
        );
        const returnedKey = headers.get("X-Guest-Key");
        if (returnedKey) setGuestKey(returnedKey);
        router.push(`/batches/${data.id}`);
        return;
      }

      const body: {
        url: string;
        inputs?: Record<string, string>;
        workflow?: string;
      } = { url: normalizedUrl };

      // Prefer topics/query inputs over mis-parsed "addresses"
      let finalInputs = { ...inputs };
      if (addresses.length === 1 && !finalInputs.address && !finalInputs.query && !finalInputs.topics) {
        finalInputs = { ...finalInputs, address: addresses[0] };
      }
      // If we somehow got multi non-address lines, treat as topics
      if (addresses.length >= 2 && !isAddressBatch) {
        finalInputs = {
          ...finalInputs,
          topics: JSON.stringify(addresses),
          query: addresses[0],
        };
      }

      if (Object.keys(finalInputs).length > 0) {
        body.inputs = finalInputs;
      }
      if (workflow) body.workflow = workflow;

      const { data, headers } = await api.post<{ id: string; total_items?: number }>(
        "/api/v1/jobs",
        body,
        guestKey,
        token,
      );
      const returnedKey = headers.get("X-Guest-Key");
      if (returnedKey) setGuestKey(returnedKey);
      if (data.total_items != null) {
        router.push(`/batches/${data.id}`);
      } else {
        router.push(`/jobs/${data.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start job");
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.form
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      onSubmit={onSubmit}
      className="console-shell flex flex-col gap-3 p-3.5 md:p-4"
    >
      <div className="mb-0.5 flex items-center gap-2 px-1 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700">
        <span className="h-1.5 w-1.5 rounded-full bg-accent/80 shadow-[0_0_8px_rgba(56,225,210,0.8)]" />
        extraction console
        <span className="ml-auto hidden text-slate-600 sm:inline">
          url → {agentInput.trim() ? "browser agent" : "extract"} → json
        </span>
      </div>
      <div className="flex flex-col gap-3 md:flex-row md:items-stretch">
        <input
          type="text"
          inputMode="url"
          required
          placeholder="https://example.com  or  example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="console-input min-w-0 flex-1 rounded-xl px-4 py-3.5 font-mono text-sm text-slate-900 outline-none placeholder:text-slate-700"
        />
        <button
          type="submit"
          disabled={loading}
          className={`btn-analyze rounded-xl px-7 py-3.5 text-sm font-semibold disabled:opacity-60 ${loading ? "is-loading" : ""}`}
        >
          <span className="relative z-[1]">{loading ? "Starting…" : "Analyze"}</span>
        </button>
      </div>
      <textarea
        rows={4}
        placeholder={
          "Optional agent inputs (same logic for every website)\n" +
            "• query: Artificial intelligence\n" +
            '• ["FastAPI","React (software)","Docker (software)"]\n' +
            "• address: 1203 Cordele Rd, Albany, GA 31705\n" +
            '• {"query":"Machine learning"}'
        }
        value={agentInput}
        onChange={(e) => setAgentInput(e.target.value)}
        className="console-input w-full resize-y rounded-xl px-4 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-700"
      />
      <p className="px-1 text-xs text-slate-700">
        Leave empty for normal extract (static / API / HTML). Add inputs to run the general
        browser agent — fill search/forms and extract results on any site. BallotReady addresses
        still use the specialized officials fast-path.
      </p>
      {error ? <p className="w-full text-left text-sm text-signal">{error}</p> : null}
    </motion.form>
  );
}
