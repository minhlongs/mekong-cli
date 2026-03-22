// Tenant Consent Management Service — CRUD for consent records and policies

export const tenantConsentManagementService = {
  async listRecords(db: any, tenantId: string): Promise<unknown[]> {
    try {
      const { results } = await db.prepare(
        `SELECT * FROM consent_records WHERE tenant_id = ? ORDER BY granted_at DESC`
      ).bind(tenantId).all();
      return results as unknown[];
    } catch (e: unknown) {
      throw new Error(`listRecords failed: ${(e as Error).message}`);
    }
  },

  async createRecord(db: any, tenantId: string, data: {
    user_id: string;
    consent_type: string;
    purpose?: string;
    granted?: number;
    ip_address?: string;
  }): Promise<unknown> {
    try {
      if (!data.user_id) throw new Error('user_id is required');
      if (!data.consent_type) throw new Error('consent_type is required');

      return db.prepare(
        `INSERT INTO consent_records (id, tenant_id, user_id, consent_type, purpose, granted, ip_address)
         VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
      ).bind(
        crypto.randomUUID(),
        tenantId,
        data.user_id,
        data.consent_type,
        data.purpose ?? null,
        data.granted ?? 1,
        data.ip_address ?? null
      ).first();
    } catch (e: unknown) {
      throw new Error(`createRecord failed: ${(e as Error).message}`);
    }
  },

  async getPolicies(db: any, tenantId: string): Promise<unknown[]> {
    try {
      const { results } = await db.prepare(
        `SELECT * FROM consent_policies WHERE tenant_id = ? AND is_active = 1 ORDER BY created_at DESC`
      ).bind(tenantId).all();
      return results as unknown[];
    } catch (e: unknown) {
      throw new Error(`getPolicies failed: ${(e as Error).message}`);
    }
  },

  async getAdminOverview(db: any): Promise<unknown> {
    try {
      const [totalRecords, grantedRecords, revokedRecords, totalPolicies, activePolicies] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM consent_records`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM consent_records WHERE granted = 1 AND revoked_at IS NULL`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM consent_records WHERE revoked_at IS NOT NULL`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM consent_policies`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM consent_policies WHERE is_active = 1`).first(),
      ]);

      return {
        records_total: (totalRecords as { count: number } | null)?.count ?? 0,
        records_granted: (grantedRecords as { count: number } | null)?.count ?? 0,
        records_revoked: (revokedRecords as { count: number } | null)?.count ?? 0,
        policies_total: (totalPolicies as { count: number } | null)?.count ?? 0,
        policies_active: (activePolicies as { count: number } | null)?.count ?? 0,
      };
    } catch (e: unknown) {
      throw new Error(`getAdminOverview failed: ${(e as Error).message}`);
    }
  },
};
