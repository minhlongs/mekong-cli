/**
 * tenant-auth.ts — Tenant authentication for mekong-raas plugin.
 * Parses Authorization header, validates mk_ prefix API keys.
 * Returns Tenant object or null for local (unauthenticated) use.
 */

import type { Tenant } from './types.js';

/** API key prefix for Mekong tenant keys */
const MEKONG_KEY_PREFIX = 'mk_';

/** Minimum length for a valid API key (prefix + 32 chars) */
const MIN_KEY_LENGTH = MEKONG_KEY_PREFIX.length + 16;

/**
 * Parse Bearer token from Authorization header value.
 * Returns the raw token string or null if not a Bearer scheme.
 */
export function parseBearerToken(authHeader: string | undefined): string | null {
  if (!authHeader) return null;
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0].toLowerCase() !== 'bearer') return null;
  const token = parts[1].trim();
  return token.length > 0 ? token : null;
}

/**
 * Validate a Mekong API key format.
 * Must start with `mk_` and be at least MIN_KEY_LENGTH characters.
 * Only alphanumeric, underscore, and hyphen characters allowed after prefix.
 */
export function isValidMekongKey(apiKey: string): boolean {
  if (!apiKey.startsWith(MEKONG_KEY_PREFIX)) return false;
  if (apiKey.length < MIN_KEY_LENGTH) return false;
  const suffix = apiKey.slice(MEKONG_KEY_PREFIX.length);
  return /^[A-Za-z0-9_-]+$/.test(suffix);
}

/**
 * Derive a stable tenantId from an API key.
 * Uses last 12 chars as a human-readable identifier suffix.
 * Production: replace with a DB/KV lookup.
 */
function deriveTenantId(apiKey: string): string {
  const suffix = apiKey.slice(-12).replace(/[^A-Za-z0-9]/g, '');
  return `tenant_${suffix}`;
}

/**
 * Resolve tenant credit balance from the API key.
 * Production: replace with a DB/KV lookup keyed by apiKey.
 * Returns a mock balance of 1000 for demonstration; real balance comes from store.
 */
function resolveCreditBalance(_apiKey: string): number {
  // Stub: real implementation fetches from Cloudflare KV / D1 / external store
  return 1000;
}

/**
 * Resolve tenant tier from the API key.
 * Production: replace with a DB/KV lookup.
 */
function resolveTier(_apiKey: string): string {
  // Stub: real implementation fetches from tenant record
  return 'pro';
}

/**
 * Authenticate a request from its Authorization header.
 *
 * Returns:
 *   - `Tenant` object if a valid `mk_*` Bearer token is present
 *   - `null` for local use (no Authorization header) — always free, not metered
 *
 * Throws:
 *   - Error with message starting with `"401:"` if header is malformed
 *   - Error with message starting with `"403:"` if key format is invalid
 */
export function authenticateTenant(
  headers: Record<string, string | undefined>,
): Tenant | null {
  const authHeader = headers['authorization'] ?? headers['Authorization'];

  // No auth header = local use = free, skip metering
  if (!authHeader) return null;

  const token = parseBearerToken(authHeader);
  if (token === null) {
    throw new Error('401: Malformed Authorization header — expected "Bearer mk_..."');
  }

  if (!isValidMekongKey(token)) {
    throw new Error('403: Invalid API key format — must start with mk_ and be at least 18 characters');
  }

  const tenantId = deriveTenantId(token);
  const creditBalance = resolveCreditBalance(token);
  const tier = resolveTier(token);

  return {
    apiKey: token,
    tenantId,
    creditBalance,
    tier,
  };
}
