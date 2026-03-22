/**
 * Mission Cost Tracking Service — records and queries LLM costs per mission
 * Supports budget management with soft/hard limits and daily/monthly resets
 */

import type { Env } from '../index';

export interface MissionCostRecord {
  tenantId: string;
  missionId: string;
  modelProvider?: string;
  modelName?: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  costUsd: number;
  computeTimeMs: number;
  creditCost: number;
}

export interface CostBreakdownRow {
  missionId: string;
  modelProvider: string | null;
  modelName: string | null;
  totalTokens: number;
  costUsd: number;
  creditCost: number;
  createdAt: string;
}

export interface BudgetConfig {
  monthlyBudgetUsd?: number | null;
  dailyBudgetUsd?: number | null;
  alertThresholdPct?: number;
  isHardLimit?: number;
}

export interface BudgetStatus {
  tenantId: string;
  monthlyBudgetUsd: number | null;
  dailyBudgetUsd: number | null;
  alertThresholdPct: number;
  currentMonthSpend: number;
  currentDaySpend: number;
  lastResetDate: string | null;
  isHardLimit: number;
  monthlyPct: number | null;
  dailyPct: number | null;
  isOverBudget: boolean;
}

export interface BudgetCheckResult {
  allowed: boolean;
  reason?: string;
  monthlyRemaining: number | null;
  dailyRemaining: number | null;
}

export class MissionCostTrackingService {
  constructor(private env: Env) {}

  /** Record a completed mission's cost */
  async recordMissionCost(data: MissionCostRecord): Promise<{ id: string }> {
    const result = await this.env.DB.prepare(
      `INSERT INTO mission_costs (tenant_id, mission_id, model_provider, model_name,
        input_tokens, output_tokens, total_tokens, cost_usd, compute_time_ms, credit_cost)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
       RETURNING id`
    )
      .bind(
        data.tenantId, data.missionId, data.modelProvider ?? null,
        data.modelName ?? null, data.inputTokens, data.outputTokens,
        data.totalTokens, data.costUsd, data.computeTimeMs, data.creditCost
      )
      .first<{ id: string }>();

    // Update budget spend counters
    await this.env.DB.prepare(
      `INSERT INTO cost_budgets (tenant_id, current_month_spend, current_day_spend, last_reset_date)
       VALUES (?, ?, ?, date('now'))
       ON CONFLICT(tenant_id) DO UPDATE SET
         current_month_spend = current_month_spend + excluded.current_month_spend,
         current_day_spend = current_day_spend + excluded.current_day_spend,
         updated_at = datetime('now')`
    )
      .bind(data.tenantId, data.costUsd, data.costUsd)
      .run();

    return { id: result?.id ?? '' };
  }

  /** Get a single mission's cost record */
  async getMissionCost(missionId: string, tenantId: string): Promise<CostBreakdownRow | null> {
    return this.env.DB.prepare(
      `SELECT mission_id as missionId, model_provider as modelProvider, model_name as modelName,
              total_tokens as totalTokens, cost_usd as costUsd, credit_cost as creditCost,
              created_at as createdAt
       FROM mission_costs WHERE mission_id = ? AND tenant_id = ?`
    )
      .bind(missionId, tenantId)
      .first<CostBreakdownRow>();
  }

  /** Aggregated cost breakdown for a tenant over N days */
  async getCostBreakdown(tenantId: string, days = 30): Promise<CostBreakdownRow[]> {
    const { results } = await this.env.DB.prepare(
      `SELECT mission_id as missionId, model_provider as modelProvider, model_name as modelName,
              total_tokens as totalTokens, cost_usd as costUsd, credit_cost as creditCost,
              created_at as createdAt
       FROM mission_costs
       WHERE tenant_id = ? AND created_at >= datetime('now', ? || ' days')
       ORDER BY created_at DESC LIMIT 500`
    )
      .bind(tenantId, `-${days}`)
      .all<CostBreakdownRow>();
    return results;
  }

  /** Cost aggregated by model over N days */
  async getCostByModel(tenantId: string, days = 30): Promise<Record<string, unknown>[]> {
    const { results } = await this.env.DB.prepare(
      `SELECT model_provider as modelProvider, model_name as modelName,
              COUNT(*) as missionCount,
              SUM(input_tokens) as inputTokens, SUM(output_tokens) as outputTokens,
              SUM(total_tokens) as totalTokens, SUM(cost_usd) as totalCostUsd,
              SUM(credit_cost) as totalCreditCost
       FROM mission_costs
       WHERE tenant_id = ? AND created_at >= datetime('now', ? || ' days')
       GROUP BY model_provider, model_name ORDER BY totalCostUsd DESC`
    )
      .bind(tenantId, `-${days}`)
      .all<Record<string, unknown>>();
    return results;
  }

  /** Daily cost totals over N days */
  async getCostByDay(tenantId: string, days = 30): Promise<Record<string, unknown>[]> {
    const { results } = await this.env.DB.prepare(
      `SELECT date(created_at) as date,
              COUNT(*) as missionCount, SUM(total_tokens) as totalTokens,
              SUM(cost_usd) as totalCostUsd, SUM(credit_cost) as totalCreditCost
       FROM mission_costs
       WHERE tenant_id = ? AND created_at >= datetime('now', ? || ' days')
       GROUP BY date(created_at) ORDER BY date DESC`
    )
      .bind(tenantId, `-${days}`)
      .all<Record<string, unknown>>();
    return results;
  }

  /** Set or update budget configuration for tenant */
  async setBudget(tenantId: string, config: BudgetConfig): Promise<void> {
    await this.env.DB.prepare(
      `INSERT INTO cost_budgets (tenant_id, monthly_budget_usd, daily_budget_usd,
         alert_threshold_pct, is_hard_limit, last_reset_date)
       VALUES (?, ?, ?, ?, ?, date('now'))
       ON CONFLICT(tenant_id) DO UPDATE SET
         monthly_budget_usd = COALESCE(excluded.monthly_budget_usd, monthly_budget_usd),
         daily_budget_usd = COALESCE(excluded.daily_budget_usd, daily_budget_usd),
         alert_threshold_pct = COALESCE(excluded.alert_threshold_pct, alert_threshold_pct),
         is_hard_limit = COALESCE(excluded.is_hard_limit, is_hard_limit),
         updated_at = datetime('now')`
    )
      .bind(
        tenantId,
        config.monthlyBudgetUsd ?? null,
        config.dailyBudgetUsd ?? null,
        config.alertThresholdPct ?? null,
        config.isHardLimit ?? null
      )
      .run();
  }

  /** Get budget status for tenant */
  async getBudget(tenantId: string): Promise<BudgetStatus | null> {
    const row = await this.env.DB.prepare(
      `SELECT tenant_id as tenantId, monthly_budget_usd as monthlyBudgetUsd,
              daily_budget_usd as dailyBudgetUsd, alert_threshold_pct as alertThresholdPct,
              current_month_spend as currentMonthSpend, current_day_spend as currentDaySpend,
              last_reset_date as lastResetDate, is_hard_limit as isHardLimit
       FROM cost_budgets WHERE tenant_id = ?`
    )
      .bind(tenantId)
      .first<Omit<BudgetStatus, 'monthlyPct' | 'dailyPct' | 'isOverBudget'>>();

    if (!row) return null;
    const monthlyPct = row.monthlyBudgetUsd ? (row.currentMonthSpend / row.monthlyBudgetUsd) * 100 : null;
    const dailyPct = row.dailyBudgetUsd ? (row.currentDaySpend / row.dailyBudgetUsd) * 100 : null;
    const isOverBudget = (monthlyPct !== null && monthlyPct >= 100) || (dailyPct !== null && dailyPct >= 100);
    return { ...row, monthlyPct, dailyPct, isOverBudget };
  }

  /** Check if estimated cost is within budget (pre-flight check) */
  async checkBudget(tenantId: string, estimatedCost: number): Promise<BudgetCheckResult> {
    const budget = await this.getBudget(tenantId);
    if (!budget) return { allowed: true, monthlyRemaining: null, dailyRemaining: null };

    const monthlyRemaining = budget.monthlyBudgetUsd !== null
      ? budget.monthlyBudgetUsd - budget.currentMonthSpend : null;
    const dailyRemaining = budget.dailyBudgetUsd !== null
      ? budget.dailyBudgetUsd - budget.currentDaySpend : null;

    if (budget.isHardLimit) {
      if (monthlyRemaining !== null && estimatedCost > monthlyRemaining)
        return { allowed: false, reason: 'Monthly budget exceeded', monthlyRemaining, dailyRemaining };
      if (dailyRemaining !== null && estimatedCost > dailyRemaining)
        return { allowed: false, reason: 'Daily budget exceeded', monthlyRemaining, dailyRemaining };
    }
    return { allowed: true, monthlyRemaining, dailyRemaining };
  }

  /** High-level cost summary for tenant dashboard */
  async getCostSummary(tenantId: string): Promise<Record<string, unknown>> {
    const [today, month, total] = await Promise.all([
      this.env.DB.prepare(
        `SELECT COUNT(*) as count, SUM(cost_usd) as costUsd, SUM(credit_cost) as creditCost
         FROM mission_costs WHERE tenant_id = ? AND date(created_at) = date('now')`
      ).bind(tenantId).first<Record<string, unknown>>(),
      this.env.DB.prepare(
        `SELECT COUNT(*) as count, SUM(cost_usd) as costUsd, SUM(credit_cost) as creditCost
         FROM mission_costs WHERE tenant_id = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')`
      ).bind(tenantId).first<Record<string, unknown>>(),
      this.env.DB.prepare(
        `SELECT COUNT(*) as count, SUM(cost_usd) as costUsd, SUM(credit_cost) as creditCost
         FROM mission_costs WHERE tenant_id = ?`
      ).bind(tenantId).first<Record<string, unknown>>(),
    ]);
    return { today, month, total };
  }

  /** Admin: cross-tenant cost overview */
  async getAdminCostOverview(): Promise<Record<string, unknown>[]> {
    const { results } = await this.env.DB.prepare(
      `SELECT tenant_id as tenantId, COUNT(*) as missionCount,
              SUM(cost_usd) as totalCostUsd, SUM(credit_cost) as totalCreditCost,
              SUM(total_tokens) as totalTokens,
              MAX(created_at) as lastMissionAt
       FROM mission_costs
       GROUP BY tenant_id ORDER BY totalCostUsd DESC LIMIT 100`
    ).all<Record<string, unknown>>();
    return results;
  }
}
