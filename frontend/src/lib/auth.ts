const ACCESS_KEY = "extractai_access";
const REFRESH_KEY = "extractai_refresh";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8100";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  email_verified?: boolean;
};

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isLoggedIn(): boolean {
  return Boolean(getAccessToken());
}

/** True when JWT looks expired (client-side check only). */
export function isAccessTokenExpired(token?: string | null): boolean {
  const raw = token ?? getAccessToken();
  if (!raw) return true;
  try {
    const parts = raw.split(".");
    if (parts.length < 2) return true;
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));
    const exp = Number(payload?.exp);
    if (!Number.isFinite(exp)) return true;
    // 30s clock skew buffer
    return Date.now() >= (exp - 30) * 1000;
  } catch {
    return true;
  }
}

/**
 * Return a usable access token, refreshing when expired.
 * Clears storage and returns null if refresh fails — callers fall back to guest.
 */
export async function getValidAccessToken(): Promise<string | null> {
  const access = getAccessToken();
  if (!access) return null;
  if (!isAccessTokenExpired(access)) return access;

  const refresh = getRefreshToken();
  if (!refresh) {
    clearTokens();
    return null;
  }

  try {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) {
      clearTokens();
      return null;
    }
    const data = (await res.json()) as {
      access_token: string;
      refresh_token: string;
    };
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}
