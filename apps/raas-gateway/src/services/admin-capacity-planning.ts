// Admin Capacity Planning Service — manage resource capacity plans and alerts

export const adminCapacityPlanningService = {
  /** List all capacity plans */
  async listPlans(db: any): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM capacity_plans ORDER BY created_at DESC`
      ).all();
      return rows.results;
    } catch (e: unknown) {
      throw new Error(`listPlans failed: ${(e as Error).message}`);
    }
  },

  /** Create a new capacity plan */
  async createPlan(db: any, data: {
    resource_type: string;
    current_usage: number;
    max_capacity: number;
    forecast_usage?: number;
    forecast_date?: string;
    status?: string;
  }): Promise<unknown> {
    try {
      const id = crypto.randomUUID();
      const result = await db.prepare(
        `INSERT INTO capacity_plans
           (id, resource_type, current_usage, max_capacity, forecast_usage, forecast_date, status)
         VALUES (?, ?, ?, ?, ?, ?, ?)
         RETURNING *`
      ).bind(
        id,
        data.resource_type,
        data.current_usage,
        data.max_capacity,
        data.forecast_usage ?? null,
        data.forecast_date ?? null,
        data.status ?? 'normal'
      ).first();
      return result;
    } catch (e: unknown) {
      throw new Error(`createPlan failed: ${(e as Error).message}`);
    }
  },

  /** List all capacity alerts (unacknowledged first) */
  async getAlerts(db: any): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM capacity_alerts ORDER BY is_acknowledged ASC, triggered_at DESC`
      ).all();
      return rows.results;
    } catch (e: unknown) {
      throw new Error(`getAlerts failed: ${(e as Error).message}`);
    }
  },

  /** Aggregate dashboard stats across all capacity plans */
  async getDashboard(db: any): Promise<unknown> {
    try {
      const [plansResult, alertsResult, byStatusResult, criticalResult] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as total, AVG(current_usage / max_capacity * 100) as avg_utilization_pct FROM capacity_plans`).first(),
        db.prepare(`SELECT COUNT(*) as total, SUM(CASE WHEN is_acknowledged = 0 THEN 1 ELSE 0 END) as unacknowledged FROM capacity_alerts`).first(),
        db.prepare(`SELECT status, COUNT(*) as count FROM capacity_plans GROUP BY status`).all(),
        db.prepare(`SELECT * FROM capacity_plans WHERE (current_usage / max_capacity) >= 0.9 ORDER BY (current_usage / max_capacity) DESC LIMIT 5`).all(),
      ]);

      // Build status breakdown map
      const byStatus: Record<string, number> = {};
      for (const row of (byStatusResult?.results ?? [])) {
        byStatus[row.status] = row.count;
      }

      return {
        total_plans: plansResult?.total ?? 0,
        avg_utilization_pct: Math.round(((plansResult?.avg_utilization_pct as number) ?? 0) * 100) / 100,
        total_alerts: alertsResult?.total ?? 0,
        unacknowledged_alerts: alertsResult?.unacknowledged ?? 0,
        plans_by_status: byStatus,
        critical_resources: criticalResult?.results ?? [],
      };
    } catch (e: unknown) {
      throw new Error(`getDashboard failed: ${(e as Error).message}`);
    }
  },
};
