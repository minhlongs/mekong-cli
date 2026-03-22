/**
 * Tenant Data Encryption Keys Service
 * Manages per-tenant data encryption keys and key usage logs
 */

// ── Types ──────────────────────────────────────────────────────────────────────

export interface EncryptionKey {
  id: string;
  tenant_id: string;
  key_name: string;
  algorithm: string;
  key_version: number;
  status: string;
  expires_at: string | null;
  created_at: string;
  rotated_at: string | null;
}

export interface KeyUsageLog {
  id: string;
  tenant_id: string;
  key_id: string;
  operation: string;
  entity_type: string | null;
  entity_id: string | null;
  created_at: string;
}

export interface CreateKeyParams {
  key_name: string;
  algorithm?: string;
  expires_at?: string;
}

export interface AdminOverview {
  tenants: number;
  total_keys: number;
  total_usage_logs: number;
  active_keys: number;
}

// ── Service ────────────────────────────────────────────────────────────────────

export const tenantDataEncryptionKeysService = {
  /** List all encryption keys for a tenant */
  async listKeys(db: any, tenantId: string): Promise<EncryptionKey[]> {
    try {
      const result = await db
        .prepare('SELECT * FROM encryption_keys WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return (result.results ?? []) as EncryptionKey[];
    } catch {
      return [];
    }
  },

  /** Create a new encryption key for a tenant */
  async createKey(db: any, tenantId: string, data: CreateKeyParams): Promise<EncryptionKey> {
    const algorithm = data.algorithm ?? 'AES-256-GCM';
    await db
      .prepare(
        `INSERT INTO encryption_keys (tenant_id, key_name, algorithm, expires_at)
         VALUES (?, ?, ?, ?)`
      )
      .bind(tenantId, data.key_name, algorithm, data.expires_at ?? null)
      .run();
    const row = await db
      .prepare('SELECT * FROM encryption_keys WHERE tenant_id = ? AND key_name = ? ORDER BY created_at DESC LIMIT 1')
      .bind(tenantId, data.key_name)
      .first();
    return row as EncryptionKey;
  },

  /** List key usage logs for a tenant */
  async getUsageLogs(db: any, tenantId: string): Promise<KeyUsageLog[]> {
    try {
      const result = await db
        .prepare('SELECT * FROM key_usage_logs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 500')
        .bind(tenantId)
        .all();
      return (result.results ?? []) as KeyUsageLog[];
    } catch {
      return [];
    }
  },

  /** Admin overview — aggregate counts across all tenants */
  async getAdminOverview(db: any): Promise<AdminOverview> {
    try {
      const [keys, logs] = await Promise.all([
        db
          .prepare(
            `SELECT COUNT(*) as total, COUNT(DISTINCT tenant_id) as tenants,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active
             FROM encryption_keys`
          )
          .first() as Promise<{ total: number; tenants: number; active: number } | null>,
        db
          .prepare('SELECT COUNT(*) as total FROM key_usage_logs')
          .first() as Promise<{ total: number } | null>,
      ]);
      return {
        tenants: keys?.tenants ?? 0,
        total_keys: keys?.total ?? 0,
        total_usage_logs: logs?.total ?? 0,
        active_keys: keys?.active ?? 0,
      };
    } catch {
      return { tenants: 0, total_keys: 0, total_usage_logs: 0, active_keys: 0 };
    }
  },
};
