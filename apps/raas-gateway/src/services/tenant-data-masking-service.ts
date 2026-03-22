/**
 * Tenant Data Masking Service
 * Manages field-level masking policies and masking event logs per tenant
 */

export const tenantDataMaskingService = {
  /** List all masking policies for a tenant */
  async listPolicies(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare(
          'SELECT * FROM data_masking_policies WHERE tenant_id = ? ORDER BY created_at DESC'
        )
        .bind(tenantId)
        .all();
      return { policies: results as any[] };
    } catch (err) {
      console.error('[data-masking] listPolicies error', err);
      throw err;
    }
  },

  /** Create a new masking policy for a tenant */
  async createPolicy(db: any, tenantId: string, data: Record<string, any>) {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO data_masking_policies
           (id, tenant_id, field_pattern, masking_type, replacement_value, applies_to, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.field_pattern,
          data.masking_type ?? 'redact',
          data.replacement_value ?? '***',
          data.applies_to ?? 'all',
          data.is_active ?? 1,
          now,
          now
        )
        .run();
      const row = await db
        .prepare('SELECT * FROM data_masking_policies WHERE id = ?')
        .bind(id)
        .first();
      return { policy: row as any };
    } catch (err) {
      console.error('[data-masking] createPolicy error', err);
      throw err;
    }
  },

  /** List masking events for a tenant, optionally filtered by policy */
  async getEvents(db: any, tenantId: string, policyId?: string) {
    try {
      let query = 'SELECT * FROM data_masking_events WHERE tenant_id = ?';
      const bindings: any[] = [tenantId];
      if (policyId) {
        query += ' AND policy_id = ?';
        bindings.push(policyId);
      }
      query += ' ORDER BY masked_at DESC LIMIT 100';
      const { results } = await db
        .prepare(query)
        .bind(...bindings)
        .all();
      return { events: results as any[] };
    } catch (err) {
      console.error('[data-masking] getEvents error', err);
      throw err;
    }
  },

  /** Admin overview — policy and event counts across all tenants */
  async getAdminOverview(db: any) {
    try {
      const [policies, events] = await Promise.all([
        db
          .prepare(
            'SELECT COUNT(*) as count, masking_type FROM data_masking_policies GROUP BY masking_type'
          )
          .all(),
        db
          .prepare(
            'SELECT COUNT(*) as count, tenant_id FROM data_masking_events GROUP BY tenant_id'
          )
          .all(),
      ]);
      return {
        policies: policies.results as any[],
        events: events.results as any[],
      };
    } catch (err) {
      console.error('[data-masking] getAdminOverview error', err);
      throw err;
    }
  },
};
