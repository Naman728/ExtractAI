const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8100";

export type ApiError = {
  error: { code: string; message: string; details?: Record<string, unknown> };
};

export { API_URL };

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as ApiError;
    return body.error?.message ?? res.statusText;
  } catch {
    return res.statusText || "Request failed";
  }
}

function authHeaders(
  guestKey?: string | null,
  token?: string | null,
  extra?: Record<string, string>,
): Record<string, string> {
  const headers: Record<string, string> = { ...(extra || {}) };
  if (guestKey) headers["X-Guest-Key"] = guestKey;
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export const api = {
  async post<T>(
    path: string,
    body: unknown,
    guestKey?: string | null,
    token?: string | null,
  ): Promise<{ data: T; headers: Headers }> {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: authHeaders(guestKey, token, { "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await parseError(res));
    return { data: (await res.json()) as T, headers: res.headers };
  },

  async get<T>(
    path: string,
    guestKey?: string | null,
    token?: string | null,
  ): Promise<T> {
    const res = await fetch(`${API_URL}${path}`, {
      headers: authHeaders(guestKey, token),
    });
    if (!res.ok) throw new Error(await parseError(res));
    return (await res.json()) as T;
  },

  /** Create a job export then download the file (auth required). */
  async downloadExport(
    jobId: string,
    format: "json" | "csv" | "excel",
    token: string,
  ): Promise<void> {
    const { data } = await api.post<{ id: string; format: string; status: string }>(
      `/api/v1/exports/${format}`,
      { job_id: jobId },
      null,
      token,
    );
    const res = await fetch(`${API_URL}/api/v1/exports/${data.id}/download`, {
      headers: authHeaders(null, token),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/i.exec(cd);
    const filename =
      match?.[1] ||
      `extractai-${jobId}.${format === "excel" ? "xlsx" : format}`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};
