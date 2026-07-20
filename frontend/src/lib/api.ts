const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8100";

export type ApiError = {
  error: { code: string; message: string; details?: Record<string, unknown> };
};

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as ApiError;
    return body.error?.message ?? res.statusText;
  } catch {
    return res.statusText || "Request failed";
  }
}

export const api = {
  async post<T>(
    path: string,
    body: unknown,
    guestKey?: string | null,
    token?: string | null,
  ): Promise<{ data: T; headers: Headers }> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (guestKey) headers["X-Guest-Key"] = guestKey;
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers,
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
    const headers: Record<string, string> = {};
    if (guestKey) headers["X-Guest-Key"] = guestKey;
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`${API_URL}${path}`, { headers });
    if (!res.ok) throw new Error(await parseError(res));
    return (await res.json()) as T;
  },
};
