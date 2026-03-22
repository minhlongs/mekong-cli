/**
 * Tenant Access Tokens Service — create, introspect, revoke, refresh tokens
 */

// ── Types ──────────────────────────────────────────────────────────────────────

export interface AccessToken {
  id: string;
  tenant_id: string;
  token_hash: string;
  token_type: string;
  scopes_json: string;
  expires_at: string;
  revoked: number;
  last_used_at: string | null;
  usage_count: number;
  created_by: string | null;
  metadata_json: string;
  created_at: string;
}

export interface RefreshToken {
  id: string;
  tenant_id: string;
  access_token_id: string;
  token_hash: string;
  expires_at: string;
  revoked: number;
  created_at: string;
}

export interface CreateTokenData {
  scopes?: string[];
  expires_in_days?: number;
  token_type?: string;
  created_by?: string;
  metadata?: Record<string, unknown>;
}

type TokenUsageRow = Pick<AccessToken, 'id' | 'usage_count' | 'last_used_at' | 'expires_at' | 'revoked'>;
type TokenListRow = Omit<AccessToken, 'token_hash'>;
type AdminTotals = { total: number; active: number; revoked: number; total_usage: number };
type TenantUsage = { tenant_id: string; token_count: number; usage: number };

// ── Helpers ────────────────────────────────────────────────────────────────────

async function hashToken(token: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

function expiresAt(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString();
}

function isExpired(ts: string): boolean {
  return new Date(ts) < new Date();
}

// ── Service ────────────────────────────────────────────────────────────────────

export const tenantAccessTokensService = {

  /** Create access + refresh token pair for tenant */
  async createToken(db: any, tenantId: string, data: CreateTokenData = {}) {
    const rawAccess = crypto.randomUUID() + '-' + crypto.randomUUID();
    const rawRefresh = crypto.randomUUID() + '-' + crypto.randomUUID();
    const accessHash = await hashToken(rawAccess);
    const refreshHash = await hashToken(rawRefresh);
    const accessId = crypto.randomUUID();
    const refreshId = crypto.randomUUID();
    const accessExpiry = expiresAt(data.expires_in_days ?? 30);
    const refreshExpiry = expiresAt((data.expires_in_days ?? 30) + 30);

    await db.prepare(
      `INSERT INTO access_tokens (id, tenant_id, token_hash, token_type, scopes_json, expires_at, created_by, metadata_json)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      accessId, tenantId, accessHash,
      data.token_type ?? 'access',
      JSON.stringify(data.scopes ?? ['read']),
      accessExpiry,
      data.created_by ?? null,
      JSON.stringify(data.metadata ?? {})
    ).run();

    await db.prepare(
      `INSERT INTO refresh_tokens (id, tenant_id, access_token_id, token_hash, expires_at)
       VALUES (?, ?, ?, ?, ?)`
    ).bind(refreshId, tenantId, accessId, refreshHash, refreshExpiry).run();

    return { access_token: rawAccess, refresh_token: rawRefresh, expires_at: accessExpiry, token_id: accessId };
  },

  /** Validate token hash — updates last_used_at and usage_count */
  async introspectToken(db: any, tokenHash: string) {
    const row = (await db.prepare(
      `SELECT * FROM access_tokens WHERE token_hash = ?`
    ).bind(tokenHash).first()) as AccessToken | null;

    if (!row) return { active: false, reason: 'not_found' };
    if (row.revoked) return { active: false, reason: 'revoked' };
    if (isExpired(row.expires_at)) return { active: false, reason: 'expired' };

    await db.prepare(
      `UPDATE access_tokens SET last_used_at = datetime('now'), usage_count = usage_count + 1 WHERE id = ?`
    ).bind(row.id).run();

    return { active: true, tenant_id: row.tenant_id, scopes: JSON.parse(row.scopes_json), expires_at: row.expires_at, token_type: row.token_type };
  },

  /** Revoke a specific access token (and its refresh tokens) */
  async revokeToken(db: any, tenantId: string, id: string) {
    await db.prepare(`UPDATE access_tokens SET revoked = 1 WHERE id = ? AND tenant_id = ?`).bind(id, tenantId).run();
    await db.prepare(`UPDATE refresh_tokens SET revoked = 1 WHERE access_token_id = ?`).bind(id).run();
    return { revoked: true };
  },

  /** List all access tokens for tenant */
  async listTokens(db: any, tenantId: string) {
    const result = await db.prepare(
      `SELECT id, token_type, scopes_json, expires_at, revoked, last_used_at, usage_count, created_by, metadata_json, created_at
       FROM access_tokens WHERE tenant_id = ? ORDER BY created_at DESC`
    ).bind(tenantId).all();
    return (result.results ?? []) as TokenListRow[];
  },

  /** Exchange refresh token for new access + refresh token pair */
  async refreshToken(db: any, refreshTokenHash: string) {
    const hashed = await hashToken(refreshTokenHash);
    const row = (await db.prepare(
      `SELECT * FROM refresh_tokens WHERE token_hash = ?`
    ).bind(hashed).first()) as RefreshToken | null;

    if (!row) return null;
    if (row.revoked || isExpired(row.expires_at)) return null;

    const parent = (await db.prepare(
      `SELECT * FROM access_tokens WHERE id = ?`
    ).bind(row.access_token_id).first()) as AccessToken | null;
    if (!parent) return null;

    // Revoke old pair before issuing new one
    await db.prepare(`UPDATE access_tokens SET revoked = 1 WHERE id = ?`).bind(parent.id).run();
    await db.prepare(`UPDATE refresh_tokens SET revoked = 1 WHERE id = ?`).bind(row.id).run();

    return this.createToken(db, row.tenant_id, {
      scopes: JSON.parse(parent.scopes_json),
      token_type: parent.token_type,
      created_by: parent.created_by ?? undefined,
      metadata: JSON.parse(parent.metadata_json),
    });
  },

  /** Revoke all access and refresh tokens for tenant */
  async revokeAllTokens(db: any, tenantId: string) {
    await db.prepare(`UPDATE access_tokens SET revoked = 1 WHERE tenant_id = ?`).bind(tenantId).run();
    await db.prepare(`UPDATE refresh_tokens SET revoked = 1 WHERE tenant_id = ?`).bind(tenantId).run();
    return { revoked_all: true };
  },

  /** Get usage stats for a specific token */
  async getTokenUsage(db: any, tenantId: string, id: string) {
    const row = (await db.prepare(
      `SELECT id, usage_count, last_used_at, expires_at, revoked FROM access_tokens WHERE id = ? AND tenant_id = ?`
    ).bind(id, tenantId).first()) as TokenUsageRow | null;
    return row ?? null;
  },

  /** Delete expired and revoked tokens (maintenance) */
  async cleanupExpired(db: any) {
    const at = await db.prepare(
      `DELETE FROM access_tokens WHERE expires_at < datetime('now') OR revoked = 1`
    ).run();
    const rt = await db.prepare(
      `DELETE FROM refresh_tokens WHERE expires_at < datetime('now') OR revoked = 1`
    ).run();
    return { deleted_access: at.meta?.changes ?? 0, deleted_refresh: rt.meta?.changes ?? 0 };
  },

  /** Admin overview of token activity across all tenants */
  async getAdminOverview(db: any) {
    const totals = (await db.prepare(
      `SELECT COUNT(*) as total,
              SUM(CASE WHEN revoked=0 AND expires_at > datetime('now') THEN 1 ELSE 0 END) as active,
              SUM(revoked) as revoked,
              SUM(usage_count) as total_usage
       FROM access_tokens`
    ).first()) as AdminTotals;

    const byTenant = await db.prepare(
      `SELECT tenant_id, COUNT(*) as token_count, SUM(usage_count) as usage
       FROM access_tokens GROUP BY tenant_id ORDER BY usage DESC LIMIT 20`
    ).all();

    return { totals, by_tenant: (byTenant.results ?? []) as TenantUsage[] };
  },
};
