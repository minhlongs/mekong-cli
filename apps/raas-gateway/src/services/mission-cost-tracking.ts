/**
 * Mission Cost Tracking Service — record and query AI provider costs per mission
 */

import { randomUUID } from 'crypto';

export interface MissionCost {
  id: string;
  tenant_id: string;
  mission_id: string;
  cost_type: string;
  amount: number;
  currency: string;
  provider?: string;
  model?: string;
  tokens_used?: number;
  created_at: string;
}

export interface CostBudget {
  id: string;
  tenant_id: string;
  monthly_limit: number;
  current_spend: number;
  alert_threshold: number;
  period_start: string;
  period_end: string;
  created_at: string;
}

export interface RecordCostData {
  mission_id: string;
  cost_type: string;
  amount: number;
  currency?: string;
  provider?: string;
  model?: string;
  tokens_used?: number;
}

export interface AdminOverview {
  total_spend: number;
  total_records: number;
  by_provider: Array<{ provider: string; total: number; count: number }>;
  by_model: Array<{ model: string; total: number; count: number }>;
  top_tenants: Array<{ tenant_id: string; total: number }>;
}

export const missionCostTrackingService = {
  /**
   * List all cost records for a tenant
   */
  async listCosts(db: any, tenantId: string): Promise<MissionCost[]> {
    try {
      const result = await db
        .prepare(
          'SELECT * FROM mission_costs WHERE tenant_id = ? ORDER BY created_at DESC'
        )
        .bind(tenantId)
        .all() as { results: MissionCost[] };
      return result.results ?? [];
    } catch (err) {
      console.error('[mission-cost-tracking] listCosts error:', err);
      return [];
    }
  },

  /**
   * Record a new cost entry for a tenant mission
   */
  async recordCost(
    db: any,
    tenantId: string,
    data: RecordCostData
  ): Promise<MissionCost | null> {
    try {
      const id = randomUUID();
      const currency = data.currency ?? 'USD';
      await db
        .prepare(
          `INSERT INTO mission_costs
            (id, tenant_id, mission_id, cost_type, amount, currency, provider, model, tokens_used)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.mission_id,
          data.cost_type,
          data.amount,
          currency,
          data.provider ?? null,
          data.model ?? null,
          data.tokens_used ?? null
        )
        .run();

      return db
        .prepare('SELECT * FROM mission_costs WHERE id = ?')
        .bind(id)
        .first();
    } catch (err) {
      console.error('[mission-cost-tracking] recordCost error:', err);
      return null;
    }
  },

  /**
   * List budget records for a tenant
   */
  async getBudgets(db: any, tenantId: string): Promise<CostBudget[]> {
    try {
      const result = await db
        .prepare(
          'SELECT * FROM cost_budgets WHERE tenant_id = ? ORDER BY created_at DESC'
        )
        .bind(tenantId)
        .all();
      return result.results ?? [];
    } catch (err) {
      console.error('[mission-cost-tracking] getBudgets error:', err);
      return [];
    }
  },

  /**
   * Admin overview: aggregated spend across all tenants
   */
  async getAdminOverview(db: any): Promise<AdminOverview> {
    try {
      const [totals, byProvider, byModel, topTenants] = await Promise.all([
        db
          .prepare(
            'SELECT COALESCE(SUM(amount), 0) as total_spend, COUNT(*) as total_records FROM mission_costs'
          )
          .first(),
        db
          .prepare(
            `SELECT COALESCE(provider, 'unknown') as provider,
              COALESCE(SUM(amount), 0) as total, COUNT(*) as count
             FROM mission_costs GROUP BY provider ORDER BY total DESC`
          )
          .all(),
        db
          .prepare(
            `SELECT COALESCE(model, 'unknown') as model,
              COALESCE(SUM(amount), 0) as total, COUNT(*) as count
             FROM mission_costs GROUP BY model ORDER BY total DESC`
          )
          .all(),
        db
          .prepare(
            `SELECT tenant_id, COALESCE(SUM(amount), 0) as total
             FROM mission_costs GROUP BY tenant_id ORDER BY total DESC LIMIT 10`
          )
          .all(),
      ]);

      return {
        total_spend: totals?.total_spend ?? 0,
        total_records: totals?.total_records ?? 0,
        by_provider: byProvider.results ?? [],
        by_model: byModel.results ?? [],
        top_tenants: topTenants.results ?? [],
      };
    } catch (err) {
      console.error('[mission-cost-tracking] getAdminOverview error:', err);
      return {
        total_spend: 0,
        total_records: 0,
        by_provider: [],
        by_model: [],
        top_tenants: [],
      };
    }
  },
};
