/**
 * Mission Cost Tracking Service — record and query execution costs per mission
 * All db calls use `db: any` (D1 binding). No generic type args. Returns { success, data/error }.
 */

export const missionCostTrackingService = {
  /** List all cost records for a tenant */
  async listCosts(db: any, tenantId: string): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
    try {
      const rows = await db
        .prepare('SELECT * FROM mission_costs WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { success: true, data: rows.results ?? [] };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** Record a new cost entry for a tenant mission */
  async createCost(
    db: any,
    tenantId: string,
    data: {
      mission_id: string;
      cost_type: string;
      amount: number;
      currency?: string;
      provider?: string;
    }
  ): Promise<{ success: boolean; data?: unknown; error?: string }> {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO mission_costs (id, tenant_id, mission_id, cost_type, amount, currency, provider, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.mission_id,
          data.cost_type,
          data.amount,
          data.currency ?? 'USD',
          data.provider ?? null,
          now
        )
        .run();
      const rows = await db
        .prepare('SELECT * FROM mission_costs WHERE id = ?')
        .bind(id)
        .all();
      return { success: true, data: (rows.results ?? [])[0] ?? null };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** List budget records for a tenant */
  async getBudgets(db: any, tenantId: string): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
    try {
      const rows = await db
        .prepare('SELECT * FROM mission_cost_budgets WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { success: true, data: rows.results ?? [] };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },

  /** Admin overview: aggregated spend across all tenants */
  async getAdminOverview(db: any): Promise<{ success: boolean; data?: unknown; error?: string }> {
    try {
      const [totals, byProvider, byTenant, budgets] = await Promise.all([
        db
          .prepare(
            'SELECT COALESCE(SUM(amount), 0) AS total_spend, COUNT(*) AS total_records FROM mission_costs'
          )
          .first(),
        db
          .prepare(
            `SELECT COALESCE(provider, 'unknown') AS provider,
               COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
             FROM mission_costs GROUP BY provider ORDER BY total DESC`
          )
          .all(),
        db
          .prepare(
            `SELECT tenant_id, COALESCE(SUM(amount), 0) AS total
             FROM mission_costs GROUP BY tenant_id ORDER BY total DESC LIMIT 10`
          )
          .all(),
        db
          .prepare('SELECT COUNT(*) AS total_budgets FROM mission_cost_budgets')
          .first(),
      ]);
      return {
        success: true,
        data: {
          total_spend: totals?.total_spend ?? 0,
          total_records: totals?.total_records ?? 0,
          total_budgets: budgets?.total_budgets ?? 0,
          by_provider: byProvider.results ?? [],
          top_tenants: byTenant.results ?? [],
        },
      };
    } catch (e: unknown) {
      return { success: false, error: (e as Error).message };
    }
  },
};
