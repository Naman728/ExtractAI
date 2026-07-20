"use client";

import { useState } from "react";

import { DashboardShell } from "@/components/dashboard/shell";
import { ComingSoonBanner } from "@/components/dashboard/coming-soon-banner";
import { useDashboardSession } from "@/components/dashboard/shared";

function generateMockKey(): string {
  const segment = () =>
    Array.from(crypto.getRandomValues(new Uint8Array(4)))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  return `ea_live_${segment()}${segment()}${segment()}`;
}

export default function ApiKeysPage() {
  const { ready } = useDashboardSession();
  const [keys, setKeys] = useState<{ id: string; label: string; prefix: string; created: string }[]>([
    { id: "1", label: "Production", prefix: "ea_live_••••••••", created: "Jul 10, 2026" },
  ]);
  const [revealed, setRevealed] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  if (!ready) return null;

  function handleGenerate() {
    const key = generateMockKey();
    setKeys((prev) => [
      {
        id: String(Date.now()),
        label: "New key",
        prefix: `${key.slice(0, 12)}••••••••`,
        created: new Date().toLocaleDateString(),
      },
      ...prev,
    ]);
    setRevealed(key);
    setCopied(false);
  }

  async function copyKey() {
    if (!revealed) return;
    await navigator.clipboard.writeText(revealed);
    setCopied(true);
  }

  return (
    <DashboardShell
      title="API Keys"
      description="Authenticate programmatic access to the ExtractAI REST API."
    >
      <ComingSoonBanner
        feature="API key management"
        detail="Keys generated here are UI placeholders only. Use JWT auth or guest keys against /api/v1 for now. Real API-key storage ships in a later phase."
      />
      <div className="mb-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleGenerate}
          className="rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-dim"
        >
          Generate new key
        </button>
        <a
          href="https://docs.extractai.dev/api"
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
        >
          API documentation →
        </a>
      </div>

      {revealed ? (
        <div className="mb-6 rounded-xl border border-teal-200 bg-teal-50 p-4 dark:border-teal-900/50 dark:bg-teal-950/30">
          <p className="text-sm font-medium text-teal-900 dark:text-teal-200">
            Copy your key now — it won&apos;t be shown again.
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <code className="flex-1 rounded-lg bg-white px-3 py-2 font-mono text-sm text-slate-800 dark:bg-slate-900 dark:text-teal-100">
              {revealed}
            </code>
            <button
              type="button"
              onClick={() => void copyKey()}
              className="rounded-lg border border-teal-300 px-3 py-2 text-sm font-medium text-teal-800 dark:border-teal-700 dark:text-teal-200"
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        </div>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
          <thead className="bg-slate-50 dark:bg-slate-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Label
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Key
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Created
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {keys.map((key) => (
              <tr key={key.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td className="px-4 py-3 text-sm font-medium text-slate-900 dark:text-white">
                  {key.label}
                </td>
                <td className="px-4 py-3 font-mono text-sm text-slate-600 dark:text-slate-400">
                  {key.prefix}
                </td>
                <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">{key.created}</td>
                <td className="px-4 py-3 text-right">
                  <button type="button" className="text-sm text-signal hover:underline">
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900/50">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Quick start</h2>
        <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
{`curl -X POST https://api.extractai.dev/api/v1/jobs \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com"}'`}
        </pre>
      </div>
    </DashboardShell>
  );
}
