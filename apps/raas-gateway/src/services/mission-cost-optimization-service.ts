/**
 * Mission Cost Optimization Service — CRUD for cost rules + events, admin overview
 * Uses db: any (D1 binding). No generic type args. All queries via .all() + cast.
 */

export const missionCostOptimizationService = {
  /** List active cost optimization rules for a tenant */
  async listRules(db: any, tenantId: string): Promise<unknown[]> {
    try {
      const rows = await db
        .prepare('SELECT * FROM cost_optimization_rules WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return rows.results as unknown[];
    } catch (e: unknown) {
      throw new Error(`listRules failed: ${(e as Error).message}`);
    }
  },

  /** Create a new cost optimization rule for a tenant */
  async createRule(
    db: any,
    tenantId: string,
    data: {
      rule_name: string;
      condition_json?: string;
      action_type?: string;
      savings_estimate?: number;
    }
  ): Promise<unknown> {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO cost_optimization_rules
             (id, tenant_id, rule_name, condition_json, action_type, savings_estimate, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.rule_name,
          data.condition_json ?? '{}',
          data.action_type ?? 'downgrade_model',
          data.savings_estimate ?? 0,
          now,
          now
        )
        .run();
      const rows = await db
        .prepare('SELECT * FROM cost_optimization_rules WHERE id = ?')
        .bind(id)
        .all();
      return (rows.results as unknown[])[0] ?? null;
    } catch (e: unknown) {
      throw new Error(`createRule failed: ${(e as Error).message}`);
    }
  },

  /** List cost optimization events for a tenant, newest first */
  async getEvents(db: any, tenantId: string, limit = 50): Promise<unknown[]> {
    try {
      const rows = await db
        .prepare(
          'SELECT * FROM cost_optimization_events WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
        )
        .bind(tenantId, limit)
        .all();
      return rows.results as unknown[];
    } catch (e: unknown) {
      throw new Error(`getEvents failed: ${(e as Error).message}`);
    }
  },

  /** Admin overview: total rules, events, and aggregate savings across all tenants */
  async getAdminOverview(db: any): Promise<unknown> {
    try {
      const [rulesRows, eventsRows] = await Promise.all([
        db.prepare('SELECT COUNT(*) as total_rules, SUM(savings_estimate) as total_estimated_savings FROM cost_optimization_rules WHERE is_active = 1').all(),
        db.prepare('SELECT COUNT(*) as total_events, SUM(savings) as total_realized_savings FROM cost_optimization_events').all(),
      ]);
      const rules = (rulesRows.results as any[])[0] ?? {};
      const events = (eventsRows.results as any[])[0] ?? {};
      return {
        total_rules: rules.total_rules ?? 0,
        total_estimated_savings: rules.total_estimated_savings ?? 0,
        total_events: events.total_events ?? 0,
        total_realized_savings: events.total_realized_savings ?? 0,
      };
    } catch (e: unknown) {
      throw new Error(`getAdminOverview failed: ${(e as Error).message}`);
    }
  },
};
