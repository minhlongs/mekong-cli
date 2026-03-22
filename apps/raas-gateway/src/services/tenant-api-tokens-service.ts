/**
 * Tenant API Tokens Service
 * Long-lived service tokens with scoped permissions, rotation, and expiry management.
 */

import type { D1Database } from '@cloudflare/workers-types';

export type TokenScope = 'read' | 'write' | 'admin' | 'missions' | 'billing';

export interface ApiToken {
  id: string;
  tenant_id: string;
  name: string;
  token_prefix: string;
  scopes: TokenScope[];
  expires_at: string | null;
  last_used_at: string | null;
  last_used_ip: string | null;
  usage_count: number;
  is_active: number;
  created_at: string;
  rotated_from: string | null;
}

/** Hash a plaintext token using SHA-256 */
async function hashToken(token: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** Generate a cryptographically random token string */
function generateRawToken(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
  return `mkt_${hex}`;
}

/** Parse scopes JSON string safely */
function parseScopes(raw: string): TokenScope[] {
  try { return JSON.parse(raw) as TokenScope[]; } catch { return ['read']; }
}

/** Create a new token — returns plaintext once, stores hash */
export async function createToken(
  db: D1Database,
  tenantId: string,
  name: string,
  scopes: TokenScope[],
  expiresIn?: number, // seconds from now
  rotatedFrom?: string,
): Promise<{ token: ApiToken; plaintext: string }> {
  const raw = generateRawToken();
  const hash = await hashToken(raw);
  const prefix = raw.slice(0, 8); // "mkt_" + 4 chars
  const id = crypto.randomUUID();
  const scopesJson = JSON.stringify(scopes);
  const expiresAt = expiresIn
    ? new Date(Date.now() + expiresIn * 1000).toISOString()
    : null;

  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO tenant_api_tokens
      (id, tenant_id, name, token_hash, token_prefix, scopes, expires_at, is_active, created_at, rotated_from)
     VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'), ?)`
  ).bind(id, tenantId, name, hash, prefix, scopesJson, expiresAt, rotatedFrom ?? null).run();

  const token: ApiToken = {
    id, tenant_id: tenantId, name, token_prefix: prefix, scopes,
    expires_at: expiresAt, last_used_at: null, last_used_ip: null,
    usage_count: 0, is_active: 1, created_at: now, rotated_from: rotatedFrom ?? null,
  };
  return { token, plaintext: raw };
}

/** List tokens for a tenant — excludes hash */
export async function listTokens(db: D1Database, tenantId: string): Promise<ApiToken[]> {
  const result = await db.prepare(
    `SELECT id, tenant_id, name, token_prefix, scopes, expires_at, last_used_at,
            last_used_ip, usage_count, is_active, created_at, rotated_from
     FROM tenant_api_tokens WHERE tenant_id = ? ORDER BY created_at DESC`
  ).bind(tenantId).all<any>();

  return (result.results ?? []).map((r) => ({ ...r, scopes: parseScopes(r.scopes) }));
}

/** Get a single token by ID */
export async function getToken(
  db: D1Database, tenantId: string, tokenId: string,
): Promise<ApiToken | null> {
  const row = await db.prepare(
    `SELECT id, tenant_id, name, token_prefix, scopes, expires_at, last_used_at,
            last_used_ip, usage_count, is_active, created_at, rotated_from
     FROM tenant_api_tokens WHERE id = ? AND tenant_id = ?`
  ).bind(tokenId, tenantId).first<any>();

  if (!row) return null;
  return { ...row, scopes: parseScopes(row.scopes) };
}

/** Revoke a token — set is_active=0 */
export async function revokeToken(
  db: D1Database, tenantId: string, tokenId: string,
): Promise<boolean> {
  const result = await db.prepare(
    `UPDATE tenant_api_tokens SET is_active = 0 WHERE id = ? AND tenant_id = ? AND is_active = 1`
  ).bind(tokenId, tenantId).run();
  return (result.meta?.changes ?? 0) > 0;
}

/** Rotate token — create new, revoke old, link via rotated_from */
export async function rotateToken(
  db: D1Database, tenantId: string, tokenId: string,
): Promise<{ token: ApiToken; plaintext: string } | null> {
  const old = await db.prepare(
    `SELECT id, name, scopes, expires_at FROM tenant_api_tokens
     WHERE id = ? AND tenant_id = ? AND is_active = 1`
  ).bind(tokenId, tenantId).first<any>();

  if (!old) return null;

  const scopes = parseScopes(old.scopes);
  // Determine remaining expiry window from original token
  const expiresIn = old.expires_at
    ? Math.max(0, Math.floor((new Date(old.expires_at).getTime() - Date.now()) / 1000))
    : undefined;

  const created = await createToken(db, tenantId, old.name, scopes, expiresIn, old.id);
  await db.prepare(
    `UPDATE tenant_api_tokens SET is_active = 0 WHERE id = ?`
  ).bind(old.id).run();

  return created;
}

/** Validate token by hash — check active + not expired, increment usage */
export async function validateToken(
  db: D1Database, tokenHash: string,
): Promise<ApiToken | null> {
  const row = await db.prepare(
    `SELECT id, tenant_id, name, token_prefix, scopes, expires_at, last_used_at,
            last_used_ip, usage_count, is_active, created_at, rotated_from
     FROM tenant_api_tokens
     WHERE token_hash = ? AND is_active = 1
       AND (expires_at IS NULL OR expires_at > datetime('now'))`
  ).bind(tokenHash).first<any>();

  if (!row) return null;

  // Increment usage count (fire-and-forget — don't block validation)
  db.prepare(
    `UPDATE tenant_api_tokens SET usage_count = usage_count + 1 WHERE id = ?`
  ).bind(row.id).run().catch(() => {});

  return { ...row, scopes: parseScopes(row.scopes) };
}

/** Update last_used_at + last_used_ip after successful validation */
export async function updateLastUsed(
  db: D1Database, tokenId: string, ip: string,
): Promise<void> {
  await db.prepare(
    `UPDATE tenant_api_tokens SET last_used_at = datetime('now'), last_used_ip = ? WHERE id = ?`
  ).bind(ip, tokenId).run();
}

/** List expired but still active tokens */
export async function getExpiredTokens(db: D1Database): Promise<ApiToken[]> {
  const result = await db.prepare(
    `SELECT id, tenant_id, name, token_prefix, scopes, expires_at, last_used_at,
            last_used_ip, usage_count, is_active, created_at, rotated_from
     FROM tenant_api_tokens
     WHERE is_active = 1 AND expires_at IS NOT NULL AND expires_at <= datetime('now')`
  ).all<any>();

  return (result.results ?? []).map((r) => ({ ...r, scopes: parseScopes(r.scopes) }));
}

/** Deactivate all expired tokens — returns count cleaned */
export async function cleanExpiredTokens(db: D1Database): Promise<number> {
  const result = await db.prepare(
    `UPDATE tenant_api_tokens SET is_active = 0
     WHERE is_active = 1 AND expires_at IS NOT NULL AND expires_at <= datetime('now')`
  ).run();
  return result.meta?.changes ?? 0;
}

/** Admin overview stats — total, active, expired, revoked, by scope */
export async function getAdminTokenOverview(db: D1Database): Promise<{
  total: number; active: number; expired: number; revoked: number;
  by_scope: Record<string, number>;
}> {
  const [totals, active, expired, scopeRows] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM tenant_api_tokens`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM tenant_api_tokens WHERE is_active = 1`).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM tenant_api_tokens
       WHERE is_active = 1 AND expires_at IS NOT NULL AND expires_at <= datetime('now')`
    ).first<{ count: number }>(),
    db.prepare(`SELECT scopes FROM tenant_api_tokens WHERE is_active = 1`).all<{ scopes: string }>(),
  ]);

  const by_scope: Record<string, number> = {};
  for (const row of scopeRows.results ?? []) {
    for (const s of parseScopes(row.scopes)) { by_scope[s] = (by_scope[s] ?? 0) + 1; }
  }

  const total = totals?.count ?? 0;
  const activeCount = active?.count ?? 0;
  return { total, active: activeCount, expired: expired?.count ?? 0, revoked: total - activeCount, by_scope };
}
