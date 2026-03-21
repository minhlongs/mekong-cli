/**
 * Tenant Lifecycle Service — core stage management
 * Stages: trial → active → growth → mature → at_risk → churned → reactivated
 * Analytics functions: see tenant-lifecycle-analytics-service.ts
 */

import type { D1Database } from '@cloudflare/workers-types';

export type LifecycleStage =
  | 'trial'
  | 'active'
  | 'growth'
  | 'mature'
  | 'at_risk'
  | 'churned'
  | 'reactivated';

export interface LifecycleRecord {
  id: string;
  tenant_id: string;
  stage: LifecycleStage;
  previous_stage: string | null;
  stage_entered_at: string;
  trial_ends_at: string | null;
  last_activity_at: string | null;
  risk_score: number;
  health_indicators: string;
  created_at: string;
}

export interface TransitionRecord {
  id: string;
  tenant_id: string;
  from_stage: string;
  to_stage: string;
  reason: string | null;
  triggered_by: string;
  metadata: string;
  created_at: string;
}

function newId(): string {
  return crypto.randomUUID();
}

/** Create initial lifecycle record for a new tenant */
export async function initLifecycle(
  db: D1Database,
  tenantId: string,
  trialDays = 14
): Promise<LifecycleRecord> {
  const id = newId();
  const trialEndsAt = new Date(Date.now() + trialDays * 86400_000).toISOString();

  await db
    .prepare(
      `INSERT INTO tenant_lifecycle (id, tenant_id, stage, trial_ends_at, last_activity_at)
       VALUES (?, ?, 'trial', ?, datetime('now'))
       ON CONFLICT(tenant_id) DO NOTHING`
    )
    .bind(id, tenantId, trialEndsAt)
    .run();

  return getLifecycleStage(db, tenantId) as Promise<LifecycleRecord>;
}

/** Get current lifecycle stage and health indicators */
export async function getLifecycleStage(
  db: D1Database,
  tenantId: string
): Promise<LifecycleRecord | null> {
  return db
    .prepare(`SELECT * FROM tenant_lifecycle WHERE tenant_id = ?`)
    .bind(tenantId)
    .first<LifecycleRecord>();
}

/** Transition tenant to a new stage and log the event */
export async function transitionStage(
  db: D1Database,
  tenantId: string,
  newStage: LifecycleStage,
  reason: string,
  triggeredBy = 'system'
): Promise<void> {
  const current = await getLifecycleStage(db, tenantId);
  if (!current) throw new Error(`No lifecycle record for tenant ${tenantId}`);
  if (current.stage === newStage) return;

  await db.batch([
    db
      .prepare(
        `UPDATE tenant_lifecycle
         SET stage = ?, previous_stage = ?, stage_entered_at = datetime('now')
         WHERE tenant_id = ?`
      )
      .bind(newStage, current.stage, tenantId),
    db
      .prepare(
        `INSERT INTO lifecycle_transitions (id, tenant_id, from_stage, to_stage, reason, triggered_by)
         VALUES (?, ?, ?, ?, ?, ?)`
      )
      .bind(newId(), tenantId, current.stage, newStage, reason, triggeredBy),
  ]);
}

/**
 * Calculate risk score 0-100 (100 = highest risk)
 * Factors: days since last activity (40%), credit balance (30%), mission frequency (30%)
 */
export async function calculateRiskScore(
  db: D1Database,
  tenantId: string
): Promise<number> {
  const [lifecycle, creditRow, missionRow] = await Promise.all([
    getLifecycleStage(db, tenantId),
    db
      .prepare(
        `SELECT COALESCE(SUM(CASE WHEN type='purchase' THEN amount ELSE -amount END), 0) as balance
         FROM credit_transactions WHERE tenant_id = ?`
      )
      .bind(tenantId)
      .first<{ balance: number }>(),
    db
      .prepare(
        `SELECT COUNT(*) as recent FROM missions
         WHERE tenant_id = ? AND created_at >= datetime('now', '-30 days')`
      )
      .bind(tenantId)
      .first<{ recent: number }>(),
  ]);

  // Days since last activity — 60d = max inactivity risk
  let inactivityScore = 50;
  if (lifecycle?.last_activity_at) {
    const days = (Date.now() - new Date(lifecycle.last_activity_at).getTime()) / 86400_000;
    inactivityScore = Math.min(100, (days / 60) * 100);
  }

  // Credit balance — 0 credits = max credit risk
  const balance = creditRow?.balance ?? 0;
  const creditScore = balance <= 0 ? 100 : Math.max(0, 100 - Math.min(100, balance * 5));

  // Mission frequency — 0 missions in 30d = max frequency risk
  const missions = missionRow?.recent ?? 0;
  const missionScore = missions === 0 ? 100 : Math.max(0, 100 - Math.min(100, missions * 10));

  const risk = Math.round(inactivityScore * 0.4 + creditScore * 0.3 + missionScore * 0.3);

  await db
    .prepare(`UPDATE tenant_lifecycle SET risk_score = ? WHERE tenant_id = ?`)
    .bind(risk, tenantId)
    .run();

  return risk;
}

/** Move a churned tenant back to reactivated */
export async function reactivateTenant(
  db: D1Database,
  tenantId: string,
  reason: string
): Promise<void> {
  const current = await getLifecycleStage(db, tenantId);
  if (!current) throw new Error(`No lifecycle record for tenant ${tenantId}`);
  if (current.stage !== 'churned') {
    throw new Error(`Tenant is not churned (current: ${current.stage})`);
  }
  await transitionStage(db, tenantId, 'reactivated', reason, 'admin');
  await db
    .prepare(
      `UPDATE tenant_lifecycle SET last_activity_at = datetime('now'), risk_score = 0 WHERE tenant_id = ?`
    )
    .bind(tenantId)
    .run();
}

/** Get full transition history for a tenant */
export async function getTransitionHistory(
  db: D1Database,
  tenantId: string
): Promise<TransitionRecord[]> {
  const result = await db
    .prepare(
      `SELECT * FROM lifecycle_transitions WHERE tenant_id = ? ORDER BY created_at DESC`
    )
    .bind(tenantId)
    .all<TransitionRecord>();
  return result.results;
}
