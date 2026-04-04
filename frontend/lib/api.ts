const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

async function parseError(res: Response): Promise<string> {
  const err = await res.json().catch(() => ({}));
  const detail = (err as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return JSON.stringify(detail);
  return res.statusText;
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{ access_token: string; token_type: string }>;
}

export async function register(email: string, password: string) {
  const res = await fetch(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{ access_token: string; token_type: string }>;
}

async function authFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function me() {
  return authFetch("/auth/me") as Promise<{ id: number; email: string }>;
}

export async function marketData(body: {
  symbol: string;
  resolution: string;
  days: number;
}) {
  return authFetch("/market/data", { method: "POST", body: JSON.stringify(body) });
}

export async function newsData(body: { symbol: string; days: number }) {
  return authFetch("/news/data", { method: "POST", body: JSON.stringify(body) });
}

export async function educationAsk(question: string) {
  return authFetch("/education/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export async function sendFeedback(body: {
  message_id: string;
  rating: 1 | -1;
  comment?: string;
}) {
  return authFetch("/feedback", { method: "POST", body: JSON.stringify(body) });
}
