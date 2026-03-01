/**
 * @agencyos/vibe-auth — Middleware Utilities
 *
 * Server-side auth utilities for JWT verification, cookie parsing,
 * and CSRF protection. Extracted from apps/apex-os middleware pattern.
 *
 * Usage:
 *   import { verifyJWT, parseCookies, validateCSRF } from '@agencyos/vibe-auth/middleware';
 */

import type { VibeAuthUser } from './types';

// ─── JWT Verification ────────────────────────────────────────────

export interface JWTPayload {
  sub: string;
  email?: string;
  role?: string;
  exp?: number;
  iat?: number;
  aud?: string;
  iss?: string;
  app_metadata?: Record<string, unknown>;
  user_metadata?: Record<string, unknown>;
}

export interface JWTVerifyResult {
  valid: boolean;
  payload: JWTPayload | null;
  error?: string;
}

/**
 * Decode and verify a JWT token (base64 decode, expiration check).
 * For cryptographic verification, use jose library on server side.
 */
export function decodeJWT(token: string): JWTVerifyResult {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return { valid: false, payload: null, error: 'Invalid JWT format' };
    }

    const payloadStr = atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'));
    const payload = JSON.parse(payloadStr) as JWTPayload;

    if (payload.exp && payload.exp * 1000 < Date.now()) {
      return { valid: false, payload, error: 'Token expired' };
    }

    return { valid: true, payload };
  } catch {
    return { valid: false, payload: null, error: 'JWT decode failed' };
  }
}

/**
 * Extract VibeAuthUser from JWT payload.
 */
export function jwtToUser(payload: JWTPayload): VibeAuthUser {
  const appMeta = payload.app_metadata ?? {};
  const userMeta = payload.user_metadata ?? {};
  const role = (appMeta['role'] as string) ?? payload.role;

  return {
    id: payload.sub,
    email: payload.email ?? '',
    name: (userMeta['full_name'] as string) ?? (userMeta['name'] as string),
    role,
    isAdmin: role === 'admin' || role === 'super_admin' || role === 'founder',
    metadata: { ...userMeta, ...appMeta },
  };
}

// ─── Cookie Parsing ──────────────────────────────────────────────

/**
 * Parse cookie header string into key-value pairs.
 */
export function parseCookies(cookieHeader: string): Record<string, string> {
  const cookies: Record<string, string> = {};
  if (!cookieHeader) return cookies;

  cookieHeader.split(';').forEach(pair => {
    const eqIdx = pair.indexOf('=');
    if (eqIdx === -1) return;
    const key = pair.substring(0, eqIdx).trim();
    const value = pair.substring(eqIdx + 1).trim();
    if (key) cookies[key] = decodeURIComponent(value);
  });

  return cookies;
}

/**
 * Extract auth token from cookies (Supabase cookie patterns).
 * Checks: sb-access-token, sb-{ref}-auth-token, custom session cookie.
 */
export function extractAuthToken(
  cookies: Record<string, string>,
  sessionCookieName?: string,
): string | null {
  if (sessionCookieName && cookies[sessionCookieName]) {
    return cookies[sessionCookieName];
  }

  if (cookies['sb-access-token']) {
    return cookies['sb-access-token'];
  }

  const supabaseCookie = Object.keys(cookies).find(
    key => key.startsWith('sb-') && key.endsWith('-auth-token'),
  );
  if (supabaseCookie) {
    return cookies[supabaseCookie];
  }

  return null;
}

// ─── CSRF Protection ─────────────────────────────────────────────

/**
 * Validate CSRF token from request headers against cookie.
 */
export function validateCSRF(
  headerToken: string | null,
  cookieToken: string | null,
): boolean {
  if (!headerToken || !cookieToken) return false;
  return headerToken === cookieToken;
}

/**
 * Check if request method is a mutation (requires CSRF).
 */
export function isMutationMethod(method: string): boolean {
  return ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase());
}

// ─── API Key Auth ────────────────────────────────────────────────

export interface APIKeyConfig {
  headerName: string;
  keys: string[];
}

/**
 * Validate API key from request header.
 */
export function validateAPIKey(
  headerValue: string | null,
  config: APIKeyConfig,
): boolean {
  if (!headerValue) return false;
  const key = headerValue.replace(/^Bearer\s+/i, '').trim();
  return config.keys.includes(key);
}

// ─── Request Auth Extraction ─────────────────────────────────────

export interface AuthExtractionResult {
  method: 'jwt' | 'api-key' | 'none';
  user: VibeAuthUser | null;
  token: string | null;
}

/**
 * Extract auth from request (tries JWT cookie → API key → none).
 */
export function extractAuth(
  cookieHeader: string,
  authHeader: string | null,
  apiKeyConfig?: APIKeyConfig,
  sessionCookieName?: string,
): AuthExtractionResult {
  // Try JWT from cookies
  const cookies = parseCookies(cookieHeader);
  const token = extractAuthToken(cookies, sessionCookieName);

  if (token) {
    const { valid, payload } = decodeJWT(token);
    if (valid && payload) {
      return { method: 'jwt', user: jwtToUser(payload), token };
    }
  }

  // Try API key
  if (apiKeyConfig && authHeader) {
    if (validateAPIKey(authHeader, apiKeyConfig)) {
      return { method: 'api-key', user: null, token: authHeader };
    }
  }

  return { method: 'none', user: null, token: null };
}
