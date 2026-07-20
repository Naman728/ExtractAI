"use client";

import { AlertTriangle } from "lucide-react";

/** Honest label for dashboard screens that are UI previews, not live backend features. */
export function ComingSoonBanner({
  feature,
  detail,
}: {
  feature: string;
  detail?: string;
}) {
  return (
    <div
      role="status"
      className="mb-6 flex gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-100"
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden />
      <div>
        <p className="font-semibold">{feature} — preview only</p>
        <p className="mt-0.5 text-amber-900/80 dark:text-amber-100/80">
          {detail ||
            "This screen is a product mock for soft launch. It is not backed by live billing, keys, or scheduling APIs yet."}
        </p>
      </div>
    </div>
  );
}
