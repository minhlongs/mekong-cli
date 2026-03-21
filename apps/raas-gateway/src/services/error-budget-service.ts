/** Error Budget Service — SLO/SLI tracking, budget calculation, and alerts */

import type { D1Database } from '@cloudflare/workers-types';

export interface SloDefinition {
  id: string;
  tenant_id: string;
  name: string;
  slo_type: 'availability' | 'latency' | 'error_rate' | 'throughput';
  target_value: number;
  window_days: number;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface ErrorBudgetStatus {
  slo_id: string;
  slo_name: string;
  slo_type: string;
  slo_target: number;
  actual_sli: number;
  error_budget_percent: number;
  budget_consumed: number;
  is_healthy: boolean;
  measurement_count: number;
}

/** Create a new SLO definition for a tenant */
export async function createSlo(db: D1Database, tenantId: string, name: string, sloType: string, targetValue: number, windowDays = 30): Promise<SloDefinition> {
  const id = crypto.randomUUID();
  await db.prepare(`INSERT INTO slo_definitions (id, tenant_id, name, slo_type, target_value, window_days) VALUES (?, ?, ?, ?, ?, ?)`)
    .bind(id, tenantId, name, sloType, targetValue, windowDays).run();
  return db.prepare(`SELECT * FROM slo_definitions WHERE id = ?`).bind(id).first<SloDefinition>() as Promise<SloDefinition>;
}

/** List all SLOs for a tenant */
export async function getSlos(db: D1Database, tenantId: string): Promise<SloDefinition[]> {
  const rows = await db.prepare(`SELECT * FROM slo_definitions WHERE tenant_id = ? ORDER BY created_at DESC`).bind(tenantId).all<SloDefinition>();
  return rows.results;
}

/** Update SLO fields (name, target_value, window_days, is_active) */
export async function updateSlo(db: D1Database, tenantId: string, sloId: string, updates: Partial<Pick<SloDefinition, 'name' | 'target_value' | 'window_days' | 'is_active'>>): Promise<void> {
  const fields = Object.keys(updates).map((k) => `${k} = ?`).join(', ');
  if (!fields) return;
  await db.prepare(`UPDATE slo_definitions SET ${fields}, updated_at = datetime('now') WHERE id = ? AND tenant_id = ?`)
    .bind(...Object.values(updates), sloId, tenantId).run();
}

/** Delete an SLO and its related data */
export async function deleteSlo(db: D1Database, tenantId: string, sloId: string): Promise<void> {
  await db.prepare(`DELETE FROM slo_definitions WHERE id = ? AND tenant_id = ?`).bind(sloId, tenantId).run();
}

/** Record a new SLI measurement for an SLO */
export async function recordMeasurement(db: D1Database, sloId: string, measuredValue: number, goodEvents = 0, totalEvents = 0): Promise<void> {
  const id = crypto.randomUUID();
  await db.prepare(`INSERT INTO sli_measurements (id, slo_id, measured_value, good_events, total_events) VALUES (?, ?, ?, ?, ?)`)
    .bind(id, sloId, measuredValue, goodEvents, totalEvents).run();
}

/** Calculate error budget for a single SLO based on measurements within window */
export async function calculateErrorBudget(
  db: D1Database,
  sloId: string
): Promise<ErrorBudgetStatus | null> {
  const slo = await db.prepare(`SELECT * FROM slo_definitions WHERE id = ?`)
    .bind(sloId).first<SloDefinition>();
  if (!slo) return null;

  const rows = await db.prepare(
    `SELECT good_events, total_events FROM sli_measurements
     WHERE slo_id = ? AND measured_at >= datetime('now', ? || ' days')`
  ).bind(sloId, `-${slo.window_days}`).all<{ good_events: number; total_events: number }>();

  const totalGood = rows.results.reduce((s, r) => s + r.good_events, 0);
  const totalEvents = rows.results.reduce((s, r) => s + r.total_events, 0);

  // SLI as percentage of good events
  const actualSli = totalEvents === 0 ? 100 : Math.round((totalGood / totalEvents) * 10000) / 100;

  // Error budget: how much of the allowed error window remains
  const allowedError = 100 - slo.target_value;   // e.g., 0.1 for 99.9%
  const actualError = 100 - actualSli;
  const budgetConsumed = allowedError === 0 ? 100 : Math.round((actualError / allowedError) * 10000) / 100;
  const errorBudgetPercent = Math.max(0, 100 - budgetConsumed);

  return {
    slo_id: sloId,
    slo_name: slo.name,
    slo_type: slo.slo_type,
    slo_target: slo.target_value,
    actual_sli: actualSli,
    error_budget_percent: errorBudgetPercent,
    budget_consumed: budgetConsumed,
    is_healthy: budgetConsumed < 100,
    measurement_count: rows.results.length,
  };
}

/** Get error budget summary for all active SLOs of a tenant */
export async function getErrorBudgetSummary(
  db: D1Database,
  tenantId: string
): Promise<ErrorBudgetStatus[]> {
  const slos = await getSlos(db, tenantId);
  const active = slos.filter((s) => s.is_active === 1);
  const results = await Promise.all(active.map((s) => calculateErrorBudget(db, s.id)));
  return results.filter(Boolean) as ErrorBudgetStatus[];
}

/** Check budget thresholds and create alerts if crossed (50%, 80%, 100% consumed) */
export async function checkAndAlert(db: D1Database, sloId: string): Promise<void> {
  const budget = await calculateErrorBudget(db, sloId);
  if (!budget) return;

  let alertType: string | null = null;
  if (budget.budget_consumed >= 100) alertType = 'exhausted';
  else if (budget.budget_consumed >= 80) alertType = 'critical';
  else if (budget.budget_consumed >= 50) alertType = 'warning';

  if (!alertType) return;

  // Avoid duplicate unacknowledged alerts of same type
  const existing = await db.prepare(
    `SELECT id FROM error_budget_alerts WHERE slo_id = ? AND alert_type = ? AND acknowledged = 0 LIMIT 1`
  ).bind(sloId, alertType).first();
  if (existing) return;

  const id = crypto.randomUUID();
  const message = `SLO "${budget.slo_name}" error budget ${alertType}: ${budget.budget_consumed.toFixed(1)}% consumed`;
  await db.prepare(
    `INSERT INTO error_budget_alerts (id, slo_id, alert_type, budget_remaining, message)
     VALUES (?, ?, ?, ?, ?)`
  ).bind(id, sloId, alertType, budget.error_budget_percent, message).run();
}

/** List alerts for a tenant; optionally filter to unacknowledged only */
export async function getAlerts(
  db: D1Database,
  tenantId: string,
  unacknowledgedOnly = false
): Promise<unknown[]> {
  const filter = unacknowledgedOnly ? 'AND a.acknowledged = 0' : '';
  const rows = await db.prepare(
    `SELECT a.* FROM error_budget_alerts a
     JOIN slo_definitions s ON s.id = a.slo_id
     WHERE s.tenant_id = ? ${filter}
     ORDER BY a.created_at DESC`
  ).bind(tenantId).all();
  return rows.results;
}

/** Acknowledge an alert by ID */
export async function acknowledgeAlert(db: D1Database, alertId: string): Promise<void> {
  await db.prepare(
    `UPDATE error_budget_alerts SET acknowledged = 1 WHERE id = ?`
  ).bind(alertId).run();
}

/** Seed default SLOs for a tenant (Mission Success 99%, API Availability 99.9%, Mission Latency p99 5000ms) */
export async function seedDefaultSlos(db: D1Database, tenantId: string): Promise<SloDefinition[]> {
  const defaults = [
    { name: 'Mission Success Rate',  sloType: 'availability', targetValue: 99.0,  windowDays: 30 },
    { name: 'API Availability',      sloType: 'availability', targetValue: 99.9,  windowDays: 30 },
    { name: 'Mission Latency p99',   sloType: 'latency',      targetValue: 5000,  windowDays: 30 },
  ];
  return Promise.all(
    defaults.map((d) => createSlo(db, tenantId, d.name, d.sloType, d.targetValue, d.windowDays))
  );
}
