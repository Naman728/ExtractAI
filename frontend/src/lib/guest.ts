const GUEST_KEY = "extractai_guest_key";

export function getGuestKey(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(GUEST_KEY);
}

export function setGuestKey(key: string): void {
  localStorage.setItem(GUEST_KEY, key);
}

export function ensureGuestKey(): string {
  const existing = getGuestKey();
  if (existing) return existing;
  const key = crypto.randomUUID();
  setGuestKey(key);
  return key;
}
