// Platform Error Budget Service — cross-service SLO budget tracking, events, and dashboard aggregation

export const platformErrorBudgetService = {
  /** List all error budgets */
  async listBudgets(db: any): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM error_budgets ORDER BY created_at DESC`
      ).all();
      return rows.results;
    } catch (e: unknown) {
      throw new Error(`listBudgets failed: ${(e as Error).message}`);
    }
  },

  /** Create a new error budget */
  async createBudget(db: any, data: {
    service_name: string;
    slo_target?: number;
    budget_remaining?: number;
    window_days?: number;
  }): Promise<unknown> {
    try {
      return await db.prepare(
        `INSERT INTO error_budgets (id, service_name, slo_target, budget_remaining, window_days, is_active, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) RETURNING *`
      ).bind(
        crypto.randomUUID(),
        data.service_name,
        data.slo_target ?? 99.9,
        data.budget_remaining ?? 100.0,
        data.window_days ?? 30
      ).first();
    } catch (e: unknown) {
      throw new Error(`createBudget failed: ${(e as Error).message}`);
    }
  },

  /** Get events for a specific budget */
  async getEvents(db: any, budgetId: string): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM error_budget_events WHERE budget_id = ? ORDER BY recorded_at DESC`
      ).bind(budgetId).all();
      return rows.results;
    } catch (e: unknown) {
      throw new Error(`getEvents failed: ${(e as Error).message}`);
    }
  },

  /** Aggregate dashboard stats across all budgets */
  async getDashboard(db: any): Promise<unknown> {
    try {
      const budgets = await db.prepare(
        `SELECT * FROM error_budgets WHERE is_active = 1 ORDER BY budget_remaining ASC`
      ).all();

      const stats = await db.prepare(
        `SELECT
           COUNT(*) AS total_budgets,
           SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_budgets,
           AVG(budget_remaining) AS avg_budget_remaining,
           MIN(budget_remaining) AS min_budget_remaining,
           SUM(CASE WHEN budget_remaining <= 0 THEN 1 ELSE 0 END) AS exhausted_count,
           SUM(CASE WHEN budget_remaining < 20 AND is_active = 1 THEN 1 ELSE 0 END) AS critical_count
         FROM error_budgets`
      ).first();

      return {
        summary: stats,
        budgets: budgets.results,
      };
    } catch (e: unknown) {
      throw new Error(`getDashboard failed: ${(e as Error).message}`);
    }
  },
};
