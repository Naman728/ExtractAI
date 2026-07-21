"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { getValidAccessToken, isLoggedIn } from "@/lib/auth";

type Format = "json" | "csv" | "excel";

const FORMATS: { id: Format; label: string }[] = [
  { id: "json", label: "JSON" },
  { id: "csv", label: "CSV" },
  { id: "excel", label: "Excel" },
];

export function ExportDownloadButtons({
  jobId,
  className = "",
}: {
  jobId: string;
  className?: string;
}) {
  const [busy, setBusy] = useState<Format | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
  }, []);

  async function download(fmt: Format) {
    setError(null);
    setBusy(fmt);
    try {
      const token = await getValidAccessToken();
      if (!token) {
        setLoggedIn(false);
        setError("Sign in to download JSON, CSV, or Excel files.");
        return;
      }
      await api.downloadExport(jobId, fmt, token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusy(null);
    }
  }

  if (!loggedIn) {
    return (
      <div className={`flex flex-wrap items-center gap-2 ${className}`}>
        <p className="text-xs font-medium text-slate-600">
          File exports (JSON / CSV / Excel) require an account.{" "}
          <Link href="/login" className="font-semibold text-accent underline">
            Sign in
          </Link>{" "}
          or{" "}
          <Link href="/register" className="font-semibold text-accent underline">
            sign up
          </Link>
          .
        </p>
        {error ? <p className="w-full text-xs font-medium text-orange-600">{error}</p> : null}
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-end gap-1 ${className}`}>
      <div className="flex flex-wrap items-center gap-2">
        {FORMATS.map((f) => (
          <button
            key={f.id}
            type="button"
            disabled={busy !== null}
            onClick={() => void download(f.id)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 transition hover:border-accent hover:text-accent disabled:opacity-50"
          >
            {busy === f.id ? `Exporting ${f.label}…` : `Download ${f.label}`}
          </button>
        ))}
      </div>
      {error ? <p className="text-xs font-medium text-orange-600">{error}</p> : null}
    </div>
  );
}
