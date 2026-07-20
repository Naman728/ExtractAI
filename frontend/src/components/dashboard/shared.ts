"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { AuthUser, getAccessToken, isLoggedIn } from "@/lib/auth";

export type JobRow = {
  id: string;
  url: string;
  status: string;
  strategy_used: string | null;
  created_at: string;
  progress_pct: number;
  batch_id?: string | null;
};

export type JobList = {
  items: JobRow[];
  total: number;
};

export function useDashboardSession() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    setToken(getAccessToken());
  }, [router]);

  const { data: user } = useQuery({
    queryKey: ["me", token],
    enabled: Boolean(token),
    queryFn: () => api.get<AuthUser>("/api/v1/auth/me", null, token),
  });

  const { data: jobs, isLoading: jobsLoading, error: jobsError } = useQuery({
    queryKey: ["jobs", token],
    enabled: Boolean(token),
    queryFn: () => api.get<JobList>("/api/v1/jobs?page=1&page_size=50", null, token),
    refetchInterval: 4000,
  });

  return { token, user, jobs, jobsLoading, jobsError, ready: Boolean(token) };
}

export function jobHref(job: JobRow): string {
  if (job.batch_id) return `/batches/${job.batch_id}`;
  if (job.status === "completed") return `/results/${job.id}`;
  return `/jobs/${job.id}`;
}

export function statusBadgeClass(status: string): string {
  switch (status) {
    case "completed":
      return "bg-teal-50 text-teal-700 ring-teal-600/20 dark:bg-teal-950/50 dark:text-teal-300 dark:ring-teal-500/30";
    case "running":
    case "pending":
      return "bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-950/50 dark:text-amber-300 dark:ring-amber-500/30";
    case "failed":
      return "bg-orange-50 text-orange-700 ring-orange-600/20 dark:bg-orange-950/50 dark:text-orange-300 dark:ring-orange-500/30";
    default:
      return "bg-slate-100 text-slate-600 ring-slate-500/20 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-500/30";
  }
}
