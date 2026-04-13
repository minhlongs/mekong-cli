/**
 * API configuration — connects to user's LOCAL Mekong Engine first,
 * falls back to cloud gateway for billing/auth only.
 */

// Local engine runs on user's machine (port 18900)
export const LOCAL_ENGINE_URL = "http://localhost:18900";

// Cloud gateway — billing, auth, credits only (NOT LLM)
export const CLOUD_API_URL = "https://api.cashclaw.cc";

// Default: try local first
export const API_BASE_URL =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  LOCAL_ENGINE_URL;

export const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

export const API_TIMEOUT_MS = 30_000;

export const DEFAULT_HEADERS: HeadersInit = {
  "Content-Type": "application/json",
  Accept: "application/json",
};

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mekong_token");
}

export function buildHeaders(extra?: HeadersInit): HeadersInit {
  const token = getAuthToken();
  return {
    ...DEFAULT_HEADERS,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}
