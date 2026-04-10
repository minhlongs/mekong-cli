/**
 * Base fetch wrapper with auth, timeout, and typed error handling.
 * Uses native fetch — no external libraries.
 */

import { API_BASE_URL, API_TIMEOUT_MS, buildHeaders } from "./api-config";
import { ApiError, type ApiResult } from "./api-types";

async function fetchWithTimeout(
  url: string,
  init: RequestInit = {}
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body?.detail ?? body?.message ?? message;
    } catch (_) {
      // ignore parse errors
    }
    throw new ApiError(res.status, message);
  }
  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
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

// ---- HTTP verbs ----

function get<T>(path: string): Promise<ApiResult<T>> {
  return safe(() =>
    fetchWithTimeout(`${API_BASE_URL}${path}`, {
      method: "GET",
      headers: buildHeaders(),
    }).then(parseResponse<T>)
  );
}

function post<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  return safe(() =>
    fetchWithTimeout(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: buildHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }).then(parseResponse<T>)
  );
}

function patch<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  return safe(() =>
    fetchWithTimeout(`${API_BASE_URL}${path}`, {
      method: "PATCH",
      headers: buildHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }).then(parseResponse<T>)
  );
}

function del<T>(path: string): Promise<ApiResult<T>> {
  return safe(() =>
    fetchWithTimeout(`${API_BASE_URL}${path}`, {
      method: "DELETE",
      headers: buildHeaders(),
    }).then(parseResponse<T>)
  );
}

export const apiClient = { get, post, patch, delete: del };
