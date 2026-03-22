/**
 * Tenant Onboarding Checklist Service — checklist init, step completion, rewards, milestones
 */

// Default steps seeded on initialization
const DEFAULT_STEPS = [
  { step_key: 'create_api_key',   step_name: 'Create your first API key',     step_order: 1, reward_credits: 5  },
  { step_key: 'submit_mission',   step_name: 'Submit your first mission',      step_order: 2, reward_credits: 10 },
  { step_key: 'setup_webhook',    step_name: 'Configure a webhook endpoint',   step_order: 3, reward_credits: 5  },
  { step_key: 'explore_models',   step_name: 'Browse the AI model registry',   step_order: 4, reward_credits: 3  },
  { step_key: 'invite_teammate',  step_name: 'Invite a teammate',              step_order: 5, reward_credits: 10 },
];

// Default milestones seeded on initialization
const DEFAULT_MILESTONES = [
  { milestone_key: 'first_mission',     milestone_name: 'First Mission Complete', reward_type: 'credits',        reward_value: '20' },
  { milestone_key: 'team_setup',        milestone_name: 'Team Ready',             reward_type: 'feature_unlock', reward_value: 'team_analytics' },
  { milestone_key: 'production_ready',  milestone_name: 'Production Ready',       reward_type: 'badge',          reward_value: 'pro_badge' },
];

/** Fetch checklist + steps for a tenant */
export async function getChecklist(db: any, tenantId: string): Promise<unknown> {
  const checklist = await db.prepare(
    'SELECT * FROM onboarding_checklists WHERE tenant_id = ?'
  ).bind(tenantId).first();
  if (!checklist) return null;

  const steps = await db.prepare(
    'SELECT * FROM onboarding_steps WHERE tenant_id = ? ORDER BY step_order ASC'
  ).bind(tenantId).all();

  return { ...checklist, steps: steps.results };
}

/** Initialize checklist with default steps and milestones (idempotent) */
export async function initializeChecklist(db: any, tenantId: string): Promise<unknown> {
  // Upsert checklist row
  const checklist = await db.prepare(
    `INSERT INTO onboarding_checklists (tenant_id) VALUES (?)
     ON CONFLICT(tenant_id) DO UPDATE SET tenant_id = tenant_id
     RETURNING *`
  ).bind(tenantId).first();

  const checklistId = (checklist as any).id;

  // Seed steps (skip if already exist)
  for (const s of DEFAULT_STEPS) {
    await db.prepare(
      `INSERT OR IGNORE INTO onboarding_steps
         (checklist_id, tenant_id, step_key, step_name, step_order, reward_credits)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).bind(checklistId, tenantId, s.step_key, s.step_name, s.step_order, s.reward_credits).run();
  }

  // Seed milestones (skip if already exist)
  for (const m of DEFAULT_MILESTONES) {
    await db.prepare(
      `INSERT OR IGNORE INTO onboarding_milestones
         (tenant_id, milestone_key, milestone_name, reward_type, reward_value)
       VALUES (?, ?, ?, ?, ?)`
    ).bind(tenantId, m.milestone_key, m.milestone_name, m.reward_type, m.reward_value).run();
  }

  return getChecklist(db, tenantId);
}

/** Mark a step as completed; recalculate overall_progress */
export async function completeStep(db: any, tenantId: string, stepKey: string): Promise<unknown> {
  const step = await db.prepare(
    'SELECT * FROM onboarding_steps WHERE tenant_id = ? AND step_key = ?'
  ).bind(tenantId, stepKey).first();
  if (!step) return { error: 'Step not found' };

  await db.prepare(
    `UPDATE onboarding_steps SET is_completed = 1, completed_at = datetime('now')
     WHERE tenant_id = ? AND step_key = ?`
  ).bind(tenantId, stepKey).run();

  await recalcProgress(db, tenantId);
  return db.prepare('SELECT * FROM onboarding_steps WHERE tenant_id = ? AND step_key = ?')
    .bind(tenantId, stepKey).first();
}

/** Claim reward credits for a completed step */
export async function claimReward(db: any, tenantId: string, stepKey: string): Promise<unknown> {
  const step = await db.prepare(
    'SELECT * FROM onboarding_steps WHERE tenant_id = ? AND step_key = ?'
  ).bind(tenantId, stepKey).first() as any;
  if (!step) return { error: 'Step not found' };
  if (!step.is_completed) return { error: 'Step not completed yet' };
  if (step.reward_claimed) return { error: 'Reward already claimed' };

  await db.prepare(
    'UPDATE onboarding_steps SET reward_claimed = 1 WHERE tenant_id = ? AND step_key = ?'
  ).bind(tenantId, stepKey).run();

  return { claimed: true, credits: step.reward_credits };
}

/** Get progress summary (percentage + step counts) */
export async function getProgress(db: any, tenantId: string): Promise<unknown> {
  const checklist = await db.prepare(
    'SELECT overall_progress, completed_at, current_step FROM onboarding_checklists WHERE tenant_id = ?'
  ).bind(tenantId).first() as any;
  if (!checklist) return null;

  const steps = await db.prepare(
    'SELECT COUNT(*) as total, SUM(is_completed) as done FROM onboarding_steps WHERE tenant_id = ?'
  ).bind(tenantId).first() as any;

  return {
    overall_progress: checklist.overall_progress,
    current_step: checklist.current_step,
    completed_at: checklist.completed_at,
    steps_total: steps?.total ?? 0,
    steps_done: steps?.done ?? 0,
  };
}

/** List milestones for a tenant */
export async function getMilestones(db: any, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    'SELECT * FROM onboarding_milestones WHERE tenant_id = ? ORDER BY created_at ASC'
  ).bind(tenantId).all();
  return rows.results;
}

/** Mark a milestone as achieved */
export async function achieveMilestone(db: any, tenantId: string, milestoneKey: string): Promise<unknown> {
  const m = await db.prepare(
    'SELECT * FROM onboarding_milestones WHERE tenant_id = ? AND milestone_key = ?'
  ).bind(tenantId, milestoneKey).first() as any;
  if (!m) return { error: 'Milestone not found' };
  if (m.is_achieved) return { error: 'Milestone already achieved' };

  await db.prepare(
    `UPDATE onboarding_milestones SET is_achieved = 1, achieved_at = datetime('now')
     WHERE tenant_id = ? AND milestone_key = ?`
  ).bind(tenantId, milestoneKey).run();

  return db.prepare('SELECT * FROM onboarding_milestones WHERE tenant_id = ? AND milestone_key = ?')
    .bind(tenantId, milestoneKey).first();
}

/** Reset checklist — delete steps/milestones, reinitialize */
export async function resetChecklist(db: any, tenantId: string): Promise<unknown> {
  await db.prepare('DELETE FROM onboarding_steps WHERE tenant_id = ?').bind(tenantId).run();
  await db.prepare('DELETE FROM onboarding_milestones WHERE tenant_id = ?').bind(tenantId).run();
  await db.prepare(
    `UPDATE onboarding_checklists
     SET overall_progress = 0, completed_at = NULL, current_step = NULL,
         started_at = datetime('now')
     WHERE tenant_id = ?`
  ).bind(tenantId).run();
  return initializeChecklist(db, tenantId);
}

/** Admin overview — aggregated stats across all tenants */
export async function getAdminOverview(db: any): Promise<unknown> {
  const [totals, completed, avgProgress] = await Promise.all([
    db.prepare('SELECT COUNT(*) as total FROM onboarding_checklists').first(),
    db.prepare('SELECT COUNT(*) as total FROM onboarding_checklists WHERE completed_at IS NOT NULL').first(),
    db.prepare('SELECT AVG(overall_progress) as avg FROM onboarding_checklists').first(),
  ]);
  return {
    total_tenants: (totals as any)?.total ?? 0,
    completed_tenants: (completed as any)?.total ?? 0,
    avg_progress: Math.round((avgProgress as any)?.avg ?? 0),
  };
}

// --- Internal helpers ---

async function recalcProgress(db: any, tenantId: string): Promise<void> {
  const row = await db.prepare(
    'SELECT COUNT(*) as total, SUM(is_completed) as done FROM onboarding_steps WHERE tenant_id = ?'
  ).bind(tenantId).first() as any;

  const total = row?.total ?? 1;
  const done = row?.done ?? 0;
  const progress = Math.round((done / total) * 100);
  const completedAt = progress === 100 ? "datetime('now')" : 'NULL';

  // Find current (next incomplete) step
  const next = await db.prepare(
    'SELECT step_key FROM onboarding_steps WHERE tenant_id = ? AND is_completed = 0 ORDER BY step_order ASC LIMIT 1'
  ).bind(tenantId).first() as any;

  await db.prepare(
    `UPDATE onboarding_checklists
     SET overall_progress = ?, completed_at = ${completedAt}, current_step = ?
     WHERE tenant_id = ?`
  ).bind(progress, next?.step_key ?? null, tenantId).run();
}
