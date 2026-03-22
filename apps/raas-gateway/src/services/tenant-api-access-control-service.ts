/**
 * Tenant API Access Control Service
 * Manages per-tenant access rules and audit log for the RaaS gateway
 */

export const tenantApiAccessControlService = {
  /** List active access rules for a tenant, ordered by priority desc */
  async listRules(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare(
          'SELECT * FROM api_access_rules WHERE tenant_id = ? AND is_active = 1 ORDER BY priority DESC, created_at DESC'
        )
        .bind(tenantId)
        .all();
      return { rules: results as any[] };
    } catch (err) {
      console.error('[access-control] listRules error', err);
      throw err;
    }
  },

  /** Create a new access rule for a tenant */
  async createRule(db: any, tenantId: string, data: Record<string, any>) {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO api_access_rules
           (id, tenant_id, resource_pattern, action, conditions_json, priority, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.resource_pattern,
          data.action ?? 'allow',
          data.conditions_json ?? '{}',
          data.priority ?? 0,
          now,
          now
        )
        .run();
      return { id, tenant_id: tenantId, ...data, is_active: 1, created_at: now, updated_at: now };
    } catch (err) {
      console.error('[access-control] createRule error', err);
      throw err;
    }
  },

  /** List audit entries for a tenant, most recent first */
  async getAudit(db: any, tenantId: string, limit = 50) {
    try {
      const { results } = await db
        .prepare(
          'SELECT * FROM api_access_audit WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
        )
        .bind(tenantId, limit)
        .all();
      return { audit: results as any[] };
    } catch (err) {
      console.error('[access-control] getAudit error', err);
      throw err;
    }
  },

  /** Admin overview — rule counts by action, recent audit activity */
  async getAdminOverview(db: any) {
    try {
      const [rulesByAction, auditByAction, totalTenants] = await Promise.all([
        db
          .prepare('SELECT action, COUNT(*) as count FROM api_access_rules WHERE is_active = 1 GROUP BY action')
          .all(),
        db
          .prepare('SELECT action_taken, COUNT(*) as count FROM api_access_audit GROUP BY action_taken')
          .all(),
        db
          .prepare('SELECT COUNT(DISTINCT tenant_id) as count FROM api_access_rules')
          .first(),
      ]);
      return {
        rulesByAction: rulesByAction.results as any[],
        auditByAction: auditByAction.results as any[],
        totalTenantsWithRules: (totalTenants as any)?.count ?? 0,
      };
    } catch (err) {
      console.error('[access-control] getAdminOverview error', err);
      throw err;
    }
  },
};
