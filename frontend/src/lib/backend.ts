export type ToolTrace = {
  name: string;
  input: Record<string, unknown>;
  output_summary: string;
};

export type DocumentCitation = {
  chunk_id: number;
  source_name: string;
  page_number?: number | null;
  section?: string | null;
  score: number;
  excerpt: string;
};

export type ChatResponse = {
  answer: string;
  sources: string[];
  tool_trace: ToolTrace[];
  chart?: {
    type: "bar" | "line";
    title: string;
    data: Array<Record<string, unknown>>;
  } | null;
  citations?: DocumentCitation[];
  sql_tables_used?: string[];
  route_kind?: string | null;
};

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "http://localhost:8000";
const API_BASE = `${BACKEND_BASE_URL}/api/v1`;
const TOKEN_KEY = "ff_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

/** Unverified parse of JWT exp (seconds since epoch). For UI only. */
export function getTokenExpiryEpoch(token: string): number | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64.length % 4 === 0 ? "" : "=".repeat(4 - (b64.length % 4));
    const payload = JSON.parse(atob(b64 + pad)) as { exp?: unknown };
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

export function isTokenFresh(token: string | null, skewSeconds = 30): boolean {
  if (!token) return false;
  const exp = getTokenExpiryEpoch(token);
  if (exp == null) return false;
  return exp > Math.floor(Date.now() / 1000) + skewSeconds;
}

export function getTokenPayload(token: string): { sub?: string; scopes?: string[] } | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64.length % 4 === 0 ? "" : "=".repeat(4 - (b64.length % 4));
    const payload = JSON.parse(atob(b64 + pad)) as { sub?: unknown; scopes?: unknown };
    const sub = typeof payload.sub === "string" ? payload.sub : undefined;
    const scopes = Array.isArray(payload.scopes) ? payload.scopes.filter((s): s is string => typeof s === "string") : undefined;
    return { sub, scopes };
  } catch {
    return null;
  }
}

export function tokenHasScope(token: string | null, scope: string): boolean {
  if (!token) return false;
  const p = getTokenPayload(token);
  return !!p?.scopes?.includes(scope);
}

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch(`${BACKEND_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(res.status === 401 ? "Invalid email or password" : `Login failed (${res.status}): ${text}`);
  }
  const json = (await res.json()) as { access_token: string };
  setToken(json.access_token);
  return json.access_token;
}

export type CreateUserResult = {
  email: string;
  first_name: string;
  last_name: string;
  temporary_password: string;
};

export async function createUser(body: { email: string; first_name: string; last_name: string }): Promise<CreateUserResult> {
  const res = await authedFetch("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    if (res.status === 401) clearToken();
    throw new Error(`Create user failed (${res.status}): ${text}`);
  }
  return (await res.json()) as CreateUserResult;
}

async function authedFetch(path: string, init: RequestInit): Promise<Response> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated");

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      Authorization: `Bearer ${token}`,
    },
  });
  const rotated = res.headers.get("x-access-token");
  if (rotated) setToken(rotated);
  if (res.status === 401) clearToken();
  return res;
}

export async function reloadDemoFromDisk(): Promise<unknown> {
  const res = await authedFetch("/demo/reload", { method: "POST" });
  if (!res.ok) {
    if (res.status === 401) clearToken();
    throw new Error(`Reload failed (${res.status}): ${await res.text()}`);
  }
  return await res.json();
}

export async function chat(question: string): Promise<ChatResponse> {
  const token = getToken();
  if (!token) throw new Error("Not authenticated");

  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });
  const rotated = res.headers.get("x-access-token");
  if (rotated) setToken(rotated);

  if (!res.ok) {
    const text = await res.text();
    if (res.status === 401) {
      clearToken();
    }
    throw new Error(`Chat failed (${res.status}): ${text}`);
  }
  return (await res.json()) as ChatResponse;
}
