/**
 * Usage Alerts Service — manages alert rules, budget configs, and trigger evaluation
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface AlertRule {
  id: string;
  tenantId: string;
  ruleType: string;
  thresholdValue: number;
  action: string;
  channel: string;
  isActive: number;
  lastTriggeredAt: string | null;
  createdAt: string;
}

export interface AlertHistory {
  id: string;
  tenantId: string;
  ruleId: string;
  ruleType: string;
  thresholdValue: number | null;
  currentValue: number | null;
  actionTaken: string | null;
  createdAt: string;
}

export interface BudgetConfig {
  id: string;
  tenantId: string;
  monthlyBudget: number | null;
  dailyBudget: number | null;
  hardLimit: number;
  rolloverUnused: number;
  budgetPeriodStart: string | null;
  createdAt: string;
  updatedAt: string | null;
}

export interface UsageSnapshot {
  creditsUsed: number;
  dailyCreditsUsed: number;
  monthlyCreditsUsed: number;
  requestRate: number;
}

// Row types for D1 queries
type AlertRuleRow = {
  id: string; tenant_id: string; rule_type: string; threshold_value: number;
  action: string; channel: string; is_active: number; last_triggered_at: string | null; created_at: string;
};
type BudgetRow = {
  id: string; tenant_id: string; monthly_budget: number | null; daily_budget: number | null;
  hard_limit: number; rollover_unused: number; budget_period_start: string | null;
  created_at: string; updated_at: string | null;
};
type AlertHistoryRow = {
  id: string; tenant_id: string; rule_id: string; rule_type: string;
  threshold_value: number | null; current_value: number | null; action_taken: string | null; created_at: string;
};

function mapRule(row: AlertRuleRow): AlertRule {
  return {
    id: row.id, tenantId: row.tenant_id, ruleType: row.rule_type,
    thresholdValue: row.threshold_value, action: row.action, channel: row.channel,
    isActive: row.is_active, lastTriggeredAt: row.last_triggered_at, createdAt: row.created_at,
  };
}

function mapBudget(row: BudgetRow): BudgetConfig {
  return {
    id: row.id, tenantId: row.tenant_id, monthlyBudget: row.monthly_budget,
    dailyBudget: row.daily_budget, hardLimit: row.hard_limit,
    rolloverUnused: row.rollover_unused, budgetPeriodStart: row.budget_period_start,
    createdAt: row.created_at, updatedAt: row.updated_at,
  };
}

/** Create a new alert rule for a tenant */
export async function createAlertRule(
  db: D1Database, tenantId: string, ruleType: string,
  thresholdValue: number, action: string, channel: string
): Promise<AlertRule> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO usage_alert_rules (id, tenant_id, rule_type, threshold_value, action, channel, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, tenantId, ruleType, thresholdValue, action, channel, now).run();
  const row = await db.prepare('SELECT * FROM usage_alert_rules WHERE id = ?').bind(id).first<AlertRuleRow>();
  if (!row) throw new Error('Failed to fetch created alert rule');
  return mapRule(row);
}

/** List all alert rules for a tenant */
export async function listAlertRules(db: D1Database, tenantId: string): Promise<AlertRule[]> {
  const result = await db.prepare(
    'SELECT * FROM usage_alert_rules WHERE tenant_id = ? ORDER BY created_at DESC'
  ).bind(tenantId).all<AlertRuleRow>();
  return result.results.map(mapRule);
}

/** Update fields on an existing alert rule */
export async function updateAlertRule(
  db: D1Database, tenantId: string, ruleId: string,
  updates: Partial<{ thresholdValue: number; action: string; channel: string; isActive: number }>
): Promise<AlertRule | null> {
  const fields: string[] = [];
  const values: unknown[] = [];
  if (updates.thresholdValue !== undefined) { fields.push('threshold_value = ?'); values.push(updates.thresholdValue); }
  if (updates.action !== undefined) { fields.push('action = ?'); values.push(updates.action); }
  if (updates.channel !== undefined) { fields.push('channel = ?'); values.push(updates.channel); }
  if (updates.isActive !== undefined) { fields.push('is_active = ?'); values.push(updates.isActive); }
  if (fields.length === 0) return null;
  values.push(ruleId, tenantId);
  await db.prepare(`UPDATE usage_alert_rules SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`)
    .bind(...values).run();
  const row = await db.prepare('SELECT * FROM usage_alert_rules WHERE id = ? AND tenant_id = ?')
    .bind(ruleId, tenantId).first<AlertRuleRow>();
  return row ? mapRule(row) : null;
}

/** Delete an alert rule (scoped to tenant) */
export async function deleteAlertRule(db: D1Database, tenantId: string, ruleId: string): Promise<boolean> {
  const result = await db.prepare(
    'DELETE FROM usage_alert_rules WHERE id = ? AND tenant_id = ?'
  ).bind(ruleId, tenantId).run();
  return (result.meta.changes ?? 0) > 0;
}

/** Evaluate all active rules against current usage, log triggers */
export async function checkAndTriggerAlerts(
  db: D1Database, tenantId: string, usage: UsageSnapshot
): Promise<AlertHistory[]> {
  const rules = await listAlertRules(db, tenantId);
  const triggered: AlertHistory[] = [];

  for (const rule of rules) {
    if (!rule.isActive) continue;
    let currentValue: number | null = null;

    if (rule.ruleType === 'credits_threshold') currentValue = usage.creditsUsed;
    else if (rule.ruleType === 'daily_limit') currentValue = usage.dailyCreditsUsed;
    else if (rule.ruleType === 'monthly_limit') currentValue = usage.monthlyCreditsUsed;
    else if (rule.ruleType === 'rate_spike') currentValue = usage.requestRate;

    if (currentValue === null || currentValue < rule.thresholdValue) continue;

    const histId = crypto.randomUUID();
    const now = new Date().toISOString();
    try {
      await db.prepare(
        `INSERT INTO usage_alert_history (id, tenant_id, rule_id, rule_type, threshold_value, current_value, action_taken, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      ).bind(histId, tenantId, rule.id, rule.ruleType, rule.thresholdValue, currentValue, rule.action, now).run();
      await db.prepare('UPDATE usage_alert_rules SET last_triggered_at = ? WHERE id = ?')
        .bind(now, rule.id).run();
      triggered.push({
        id: histId, tenantId, ruleId: rule.id, ruleType: rule.ruleType,
        thresholdValue: rule.thresholdValue, currentValue, actionTaken: rule.action, createdAt: now,
      });
    } catch { /* non-critical — continue */ }
  }
  return triggered;
}

/** Fetch alert trigger history for a tenant */
export async function getAlertHistory(
  db: D1Database, tenantId: string, limit = 50
): Promise<AlertHistory[]> {
  const result = await db.prepare(
    'SELECT * FROM usage_alert_history WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
  ).bind(tenantId, limit).all<AlertHistoryRow>();
  return result.results.map(row => ({
    id: row.id, tenantId: row.tenant_id, ruleId: row.rule_id, ruleType: row.rule_type,
    thresholdValue: row.threshold_value, currentValue: row.current_value,
    actionTaken: row.action_taken, createdAt: row.created_at,
  }));
}

/** Upsert budget config for a tenant */
export async function setBudgetConfig(
  db: D1Database, tenantId: string,
  config: Partial<{ monthlyBudget: number; dailyBudget: number; hardLimit: number }>
): Promise<BudgetConfig> {
  const existing = await db.prepare('SELECT id FROM budget_configs WHERE tenant_id = ?')
    .bind(tenantId).first<{ id: string }>();
  const now = new Date().toISOString();
  if (existing) {
    await db.prepare(
      `UPDATE budget_configs SET monthly_budget = ?, daily_budget = ?, hard_limit = ?, updated_at = ?
       WHERE tenant_id = ?`
    ).bind(config.monthlyBudget ?? null, config.dailyBudget ?? null, config.hardLimit ?? 0, now, tenantId).run();
  } else {
    const id = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO budget_configs (id, tenant_id, monthly_budget, daily_budget, hard_limit, created_at)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).bind(id, tenantId, config.monthlyBudget ?? null, config.dailyBudget ?? null, config.hardLimit ?? 0, now).run();
  }
  const row = await db.prepare('SELECT * FROM budget_configs WHERE tenant_id = ?')
    .bind(tenantId).first<BudgetRow>();
  if (!row) throw new Error('Failed to fetch budget config');
  return mapBudget(row);
}

/** Get budget config for a tenant */
export async function getBudgetConfig(db: D1Database, tenantId: string): Promise<BudgetConfig | null> {
  const row = await db.prepare('SELECT * FROM budget_configs WHERE tenant_id = ?')
    .bind(tenantId).first<BudgetRow>();
  return row ? mapBudget(row) : null;
}

/** Check if a request is within budget; returns { allowed, reason } */
export async function checkBudgetLimit(
  db: D1Database, tenantId: string, requestedCredits: number
): Promise<{ allowed: boolean; reason?: string; hardBlock: boolean }> {
  const budget = await getBudgetConfig(db, tenantId);
  if (!budget) return { allowed: true, hardBlock: false };

  if (budget.dailyBudget !== null && requestedCredits > budget.dailyBudget) {
    return { allowed: !budget.hardLimit, hardBlock: !!budget.hardLimit, reason: 'daily_budget_exceeded' };
  }
  if (budget.monthlyBudget !== null && requestedCredits > budget.monthlyBudget) {
    return { allowed: !budget.hardLimit, hardBlock: !!budget.hardLimit, reason: 'monthly_budget_exceeded' };
  }
  return { allowed: true, hardBlock: false };
}

/** Admin: most triggered rules and budget utilization across all tenants */
export async function getAdminAlertOverview(db: D1Database): Promise<{
  topTriggeredRules: { ruleType: string; triggerCount: number }[];
  tenantsWithBudget: number;
  tenantsWithHardLimit: number;
}> {
  const [triggeredResult, budgetResult] = await Promise.all([
    db.prepare(
      `SELECT rule_type, COUNT(*) as trigger_count FROM usage_alert_history
       GROUP BY rule_type ORDER BY trigger_count DESC LIMIT 10`
    ).all<{ rule_type: string; trigger_count: number }>(),
    db.prepare(
      'SELECT COUNT(*) as total, SUM(hard_limit) as hard FROM budget_configs'
    ).first<{ total: number; hard: number }>(),
  ]);

  return {
    topTriggeredRules: triggeredResult.results.map(r => ({
      ruleType: r.rule_type, triggerCount: r.trigger_count,
    })),
    tenantsWithBudget: budgetResult?.total ?? 0,
    tenantsWithHardLimit: budgetResult?.hard ?? 0,
  };
}
