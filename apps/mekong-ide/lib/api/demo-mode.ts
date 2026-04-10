/**
 * Demo mode helpers — detect if the gateway API is reachable,
 * fall back to mock data when offline.
 */

import { API_BASE_URL } from "./api-config";

let cachedReachable: boolean | null = null;
let lastCheckMs = 0;
const CACHE_TTL_MS = 30_000;

/**
 * Check if the gateway is reachable by hitting /health.
 * Result is cached for 30 s to avoid repeated probes.
 */
export async function isApiReachable(): Promise<boolean> {
  const now = Date.now();
  if (cachedReachable !== null && now - lastCheckMs < CACHE_TTL_MS) {
    return cachedReachable;
  }
  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      signal: AbortSignal.timeout(3_000),
    });
    cachedReachable = res.ok;
  } catch (_) {
    cachedReachable = false;
  }
  lastCheckMs = Date.now();
  return cachedReachable;
}

/** Invalidate the cache — call after user manually reconnects */
export function resetReachabilityCache() {
  cachedReachable = null;
  lastCheckMs = 0;
}

/**
 * Wrap an API call with demo-mode fallback.
 * If the call fails AND the API is unreachable, returns mock data
 * and sets isDemoMode = true on the result.
 */
export async function withDemoFallback<T>(
  apiCall: () => Promise<T>,
  mockData: T
): Promise<{ data: T; isDemoMode: boolean }> {
  try {
    const data = await apiCall();
    return { data, isDemoMode: false };
  } catch (err) {
    const reachable = await isApiReachable();
    if (!reachable) {
      return { data: mockData, isDemoMode: true };
    }
    throw err;
  }
}
