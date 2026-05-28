/**
 * API client — routes through Rust IPC in Tauri, native fetch in browser.
 *
 * The Tauri path uses window.__TAURI_INTERNALS__.invoke() directly.
 * Both code paths are ALWAYS included — no conditional imports, no
 * tree-shakeable branches. The runtime check happens inside apiCall().
 */
"use client";

import { API_BASE_URL, API_TIMEOUT_MS, buildHeaders } from "./api-config";
import { ApiError, type ApiResult } from "./api-types";

/* eslint-disable @typescript-eslint/no-explicit-any */

// Force bundler to include this string by assigning to a module-level const
const TAURI_CMD = "gateway_fetch";
const TAURI_KEY = "__TAURI_INTERNALS__";

/** Unified API call — tries Tauri IPC first, falls back to fetch */
async function apiCall<T>(
  path: string,
  method: string,
  body?: unknown
): Promise<T> {
  // Tauri path — use window global directly (no import)
  if (typeof globalThis !== "undefined") {
    const internals = (globalThis as any)[TAURI_KEY];
    if (internals && typeof internals.invoke === "function") {
      return internals.invoke(TAURI_CMD, {
        path,
        method,
        body: body !== undefined ? JSON.stringify(body) : null,
      }) as Promise<T>;
    }
  }

  // Browser path — standard fetch
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
      } catch (_) {
        // ignore JSON parsing errors for error responses
      }
      throw new ApiError(res.status, message);
    }
    if (res.status === 204) return undefined as unknown as T;
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
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
