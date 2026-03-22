/**
 * Tenant API Key Management Service
 * CRUD + rotate + scopes + usage logging for tenant-scoped API keys.
 */

// --- helpers ---

async function hashKey(raw: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

function parseScopes(json: string): string[] {
  try { return JSON.parse(json); } catch { return ['read']; }
}

function generateRaw(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return 'mk_' + Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
}

// --- service ---

export const tenantApiKeyService = {

  /** List all keys for a tenant — never returns full key or hash */
  async listKeys(db: any, tenantId: string) {
    const result = await db.prepare(
      `SELECT id, tenant_id, name, key_prefix, scopes_json, status, expires_at,
              last_used_at, usage_count, created_at, revoked_at
       FROM api_keys WHERE tenant_id = ? ORDER BY created_at DESC`
    ).bind(tenantId).all();
    return ((result.results ?? []) as any[]).map((r) => ({ ...r, scopes: parseScopes(r.scopes_json) }));
  },

  /** Create a new key — returns plaintext key ONCE */
  async createKey(db: any, tenantId: string, data: { name: string; scopes?: string[]; expires_at?: string }) {
    const raw = generateRaw();
    const hash = await hashKey(raw);
    const id = crypto.randomUUID();
    const prefix = raw.slice(0, 7); // "mk_" + 4 chars
    const scopesJson = JSON.stringify(data.scopes ?? ['read']);

    await db.prepare(
      `INSERT INTO api_keys (id, tenant_id, name, key_hash, key_prefix, scopes_json, status, expires_at, created_at)
       VALUES (?, ?, ?, ?, ?, ?, 'active', ?, CURRENT_TIMESTAMP)`
    ).bind(id, tenantId, data.name, hash, prefix, scopesJson, data.expires_at ?? null).run();

    return { id, name: data.name, key_prefix: prefix, scopes: data.scopes ?? ['read'],
      expires_at: data.expires_at ?? null, key: raw,
      hint: 'Store this key securely — it will not be shown again' };
  },

  /** Get key metadata by id (no hash returned) */
  async getKey(db: any, tenantId: string, id: string) {
    const row = await db.prepare(
      `SELECT id, tenant_id, name, key_prefix, scopes_json, status, expires_at,
              last_used_at, usage_count, created_at, revoked_at
       FROM api_keys WHERE id = ? AND tenant_id = ?`
    ).bind(id, tenantId).first();
    if (!row) return null;
    return { ...row, scopes: parseScopes((row as any).scopes_json) };
  },

  /** Revoke a key — soft delete */
  async revokeKey(db: any, tenantId: string, id: string): Promise<boolean> {
    const result = await db.prepare(
      `UPDATE api_keys SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP
       WHERE id = ? AND tenant_id = ? AND status = 'active'`
    ).bind(id, tenantId).run();
    return (result.meta?.changes ?? 0) > 0;
  },

  /** Rotate — revoke old key, create new with same scopes */
  async rotateKey(db: any, tenantId: string, id: string) {
    const old = await db.prepare(
      `SELECT id, name, scopes_json, expires_at FROM api_keys
       WHERE id = ? AND tenant_id = ? AND status = 'active'`
    ).bind(id, tenantId).first();
    if (!old) return null;
    const oldKey = old as any;

    const scopes = parseScopes(oldKey.scopes_json);
    const raw = generateRaw();
    const hash = await hashKey(raw);
    const newId = crypto.randomUUID();
    const prefix = raw.slice(0, 7);

    await db.batch([
      db.prepare(`UPDATE api_keys SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP WHERE id = ?`).bind(oldKey.id),
      db.prepare(
        `INSERT INTO api_keys (id, tenant_id, name, key_hash, key_prefix, scopes_json, status, expires_at, created_at)
         VALUES (?, ?, ?, ?, ?, ?, 'active', ?, CURRENT_TIMESTAMP)`
      ).bind(newId, tenantId, oldKey.name, hash, prefix, oldKey.scopes_json, oldKey.expires_at ?? null),
    ]);

    return { id: newId, name: oldKey.name, key_prefix: prefix, scopes,
      key: raw, hint: 'Previous key revoked — store this new key securely' };
  },

  /** Update scopes for an active key */
  async updateScopes(db: any, tenantId: string, id: string, scopes: string[]): Promise<boolean> {
    const result = await db.prepare(
      `UPDATE api_keys SET scopes_json = ? WHERE id = ? AND tenant_id = ? AND status = 'active'`
    ).bind(JSON.stringify(scopes), id, tenantId).run();
    return (result.meta?.changes ?? 0) > 0;
  },

  /** Paginated usage logs for a key */
  async getUsageLogs(db: any, tenantId: string, keyId: string, limit = 50, offset = 0) {
    // Verify key belongs to tenant
    const key = await db.prepare(`SELECT id FROM api_keys WHERE id = ? AND tenant_id = ?`)
      .bind(keyId, tenantId).first();
    if (!key) return null;

    const result = await db.prepare(
      `SELECT id, api_key_id, endpoint, method, status_code, ip_address, created_at
       FROM api_key_usage_logs WHERE api_key_id = ?
       ORDER BY created_at DESC LIMIT ? OFFSET ?`
    ).bind(keyId, limit, offset).all();
    return { logs: result.results ?? [], limit, offset };
  },

  /** Record a usage log entry (fire-and-forget safe) */
  async recordUsage(db: any, keyId: string, endpoint: string, method: string, statusCode: number, ip: string) {
    const id = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO api_key_usage_logs (id, api_key_id, endpoint, method, status_code, ip_address, created_at)
       VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`
    ).bind(id, keyId, endpoint, method, statusCode, ip).run();
    // Also update last_used_at + usage_count on the key
    await db.prepare(
      `UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP, usage_count = usage_count + 1 WHERE id = ?`
    ).bind(keyId).run();
  },

  /** Admin overview: total/active/revoked key counts */
  async getAdminOverview(db: any) {
    const [total, active, revoked] = await Promise.all([
      db.prepare(`SELECT COUNT(*) as count FROM api_keys`).first(),
      db.prepare(`SELECT COUNT(*) as count FROM api_keys WHERE status = 'active'`).first(),
      db.prepare(`SELECT COUNT(*) as count FROM api_keys WHERE status = 'revoked'`).first(),
    ]);
    return {
      total: (total as any)?.count ?? 0,
      active: (active as any)?.count ?? 0,
      revoked: (revoked as any)?.count ?? 0,
    };
  },
};
