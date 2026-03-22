/**
 * Tenant Secret Vault Service
 * CRUD for encrypted tenant secrets + access audit log queries
 */

function newId(): string {
  return crypto.randomUUID();
}

export const tenantSecretVaultService = {
  /**
   * List all secrets for a tenant (names + metadata, no encrypted values)
   */
  async listSecrets(db: any, tenantId: string) {
    try {
      const result = await db
        .prepare(
          `SELECT id, tenant_id, secret_name, secret_type, expires_at, created_at, updated_at
           FROM tenant_secrets WHERE tenant_id = ? ORDER BY created_at DESC`
        )
        .bind(tenantId)
        .all();
      return (result.results ?? []) as Record<string, unknown>[];
    } catch (err) {
      console.error('[secretVault] listSecrets error:', err);
      throw err;
    }
  },

  /**
   * Create a new secret entry for a tenant
   */
  async createSecret(
    db: any,
    tenantId: string,
    body: { secret_name: string; encrypted_value: string; secret_type?: string; expires_at?: string }
  ) {
    try {
      const id = newId();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO tenant_secrets (id, tenant_id, secret_name, encrypted_value, secret_type, expires_at, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          body.secret_name,
          body.encrypted_value,
          body.secret_type ?? 'api_key',
          body.expires_at ?? null,
          now,
          now
        )
        .run();
      return { id, tenant_id: tenantId, secret_name: body.secret_name, created_at: now };
    } catch (err) {
      console.error('[secretVault] createSecret error:', err);
      throw err;
    }
  },

  /**
   * Get access logs for a tenant's secrets, optionally filtered by secret_id
   */
  async getAccessLogs(db: any, tenantId: string, secretId?: string) {
    try {
      const query = secretId
        ? `SELECT * FROM secret_access_logs WHERE tenant_id = ? AND secret_id = ? ORDER BY accessed_at DESC LIMIT 100`
        : `SELECT * FROM secret_access_logs WHERE tenant_id = ? ORDER BY accessed_at DESC LIMIT 100`;
      const stmt = secretId
        ? db.prepare(query).bind(tenantId, secretId)
        : db.prepare(query).bind(tenantId);
      const result = await stmt.all();
      return (result.results ?? []) as Record<string, unknown>[];
    } catch (err) {
      console.error('[secretVault] getAccessLogs error:', err);
      throw err;
    }
  },

  /**
   * Admin overview: secret counts + recent access activity across all tenants
   */
  async getAdminOverview(db: any) {
    try {
      const counts = await db
        .prepare(
          `SELECT tenant_id, COUNT(*) as secret_count, MAX(updated_at) as last_updated
           FROM tenant_secrets GROUP BY tenant_id ORDER BY secret_count DESC LIMIT 50`
        )
        .all();
      const recentLogs = await db
        .prepare(
          `SELECT * FROM secret_access_logs ORDER BY accessed_at DESC LIMIT 20`
        )
        .all();
      return {
        tenants: (counts.results ?? []) as Record<string, unknown>[],
        recent_access: (recentLogs.results ?? []) as Record<string, unknown>[],
      };
    } catch (err) {
      console.error('[secretVault] getAdminOverview error:', err);
      throw err;
    }
  },
};
