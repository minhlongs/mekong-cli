/**
 * API client — routes through Rust IPC in Tauri, native fetch in browser.
 *
 * IMPORTANT: Tauri detection must be runtime-only (not tree-shakeable).
 * Next.js SSG eliminates code paths it evaluates as dead at build time.
 * All Tauri imports MUST be dynamic import() inside runtime functions.
 */

import { API_BASE_URL, API_TIMEOUT_MS, buildHeaders } from "./api-config";
import { ApiError, type ApiResult } from "./api-types";

/** Runtime check — NOT tree-shakeable because it depends on window */
function isInTauri(): boolean {
  try {
    return typeof window !== "undefined" &&
      typeof (window as Record<string, unknown>)["__TAURI_INTERNALS__"] !== "undefined";
  } catch {
    return false;
  }
}

/** Route API call through Rust IPC (bypasses WebView sandbox) */
async function tauriFetch<T>(
  path: string,
  method: string,
  body?: unknown
): Promise<T> {
  // Dynamic import — MUST stay inside function body to survive tree-shaking
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<T>("gateway_fetch", {
    path,
    method,
    body: body !== undefined ? JSON.stringify(body) : null,
  });
}

/** Standard browser fetch with timeout */
async function browserFetch<T>(
  path: string,
  method: string,
  body?: unknown
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: buildHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (!res.ok) {
      let message = `HTTP ${res.status}`;
      try {
        const data = await res.json();
        message = data?.detail ?? data?.message ?? message;
      } catch {}
      throw new ApiError(res.status, message);
    }
    if (res.status === 204) return undefined as unknown as T;
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
}

/** Unified API call — Tauri IPC or browser fetch */
async function apiCall<T>(
  path: string,
  method: string,
  body?: unknown
): Promise<T> {
  // Runtime check every call — not cached, not tree-shakeable
  if (isInTauri()) {
    return tauriFetch<T>(path, method, body);
  }
  return browserFetch<T>(path, method, body);
}

/** Wrap any API call into {data, error} — never throws */
async function safe<T>(call: () => Promise<T>): Promise<ApiResult<T>> {
  try {
    const data = await call();
    return { data, error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return { data: null, error: message };
  }
}

function get<T>(path: string): Promise<ApiResult<T>> {
  return safe(() => apiCall<T>(path, "GET"));
}

function post<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  return safe(() => apiCall<T>(path, "POST", body));
}

function patch<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  return safe(() => apiCall<T>(path, "PATCH", body));
}

function del<T>(path: string): Promise<ApiResult<T>> {
  return safe(() => apiCall<T>(path, "DELETE"));
}

export const apiClient = { get, post, patch, delete: del };
