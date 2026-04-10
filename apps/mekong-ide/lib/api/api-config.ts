/**
 * API configuration — base URL, default headers, timeout.
 * Reads NEXT_PUBLIC_API_URL from env, defaults to localhost:8000.
 */

export const API_BASE_URL =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

export const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

/** Default timeout in milliseconds */
export const API_TIMEOUT_MS = 30_000;

export const DEFAULT_HEADERS: HeadersInit = {
  "Content-Type": "application/json",
  Accept: "application/json",
};

/** Read auth token from localStorage (browser only) */
export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mekong_token");
}

/** Build headers including optional Bearer token */
export function buildHeaders(extra?: HeadersInit): HeadersInit {
  const token = getAuthToken();
  return {
    ...DEFAULT_HEADERS,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}
