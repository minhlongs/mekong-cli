/**
 * Onboarding V2 Service — wizard flow, step tracking, defaults seeding, analytics
 * Steps: welcome → profile_setup → api_key_creation → first_mission →
 *        webhook_setup → team_invite → billing_setup → security_setup
 */

import type { D1Database } from '@cloudflare/workers-types';
import { nextStep, calcProgress, parseFlow, logEvent } from './onboarding-v2-helpers';

export const ONBOARDING_STEPS = [
  'welcome',
  'profile_setup',
  'api_key_creation',
  'first_mission',
  'webhook_setup',
  'team_invite',
  'billing_setup',
  'security_setup',
] as const;

export type OnboardingStep = typeof ONBOARDING_STEPS[number];

const STEP_REASONS: Record<string, string> = {
  welcome: 'Start your onboarding journey',
  profile_setup: 'Complete your profile to personalise the experience',
  api_key_creation: 'Create an API key to integrate your first app',
  first_mission: 'Run a mission to see the platform in action',
  webhook_setup: 'Set up webhooks for real-time event notifications',
  team_invite: 'Invite teammates to collaborate',
  billing_setup: 'Add a payment method to avoid service interruption',
  security_setup: 'Enable MFA and IP allowlisting for security',
};

export interface OnboardingFlow {
  id: string;
  tenant_id: string;
  current_step: string;
  completed_steps: string[];
  skipped_steps: string[];
  metadata: Record<string, unknown>;
  started_at: string;
  completed_at: string | null;
  status: 'in_progress' | 'completed' | 'abandoned';
}

export interface OnboardingStatus extends OnboardingFlow {
  progress_pct: number;
  next_step: string | null;
}

// ─── Public API ──────────────────────────────────────────────────────────────

/** Create onboarding flow for tenant (idempotent) */
export async function startOnboarding(db: D1Database, tenantId: string): Promise<OnboardingFlow> {
  const existing = await db
    .prepare('SELECT * FROM onboarding_flows WHERE tenant_id = ?')
    .bind(tenantId)
    .first<Record<string, unknown>>();
  if (existing) return parseFlow(existing);

  const id = crypto.randomUUID();
  await db
    .prepare(
      `INSERT INTO onboarding_flows (id, tenant_id, current_step, completed_steps, skipped_steps, metadata, status)
       VALUES (?, ?, 'welcome', '[]', '[]', '{}', 'in_progress')`,
    )
    .bind(id, tenantId)
    .run();
  await logEvent(db, tenantId, 'welcome', 'started');

  const row = await db
    .prepare('SELECT * FROM onboarding_flows WHERE id = ?')
    .bind(id)
    .first<Record<string, unknown>>();
  return parseFlow(row!);
}

/** Return current status with progress percentage */
export async function getOnboardingStatus(
  db: D1Database,
  tenantId: string,
): Promise<OnboardingStatus | null> {
  const row = await db
    .prepare('SELECT * FROM onboarding_flows WHERE tenant_id = ?')
    .bind(tenantId)
    .first<Record<string, unknown>>();
  if (!row) return null;

  const flow = parseFlow(row);
  return {
    ...flow,
    progress_pct: calcProgress(flow.completed_steps, flow.skipped_steps),
    next_step: nextStep(flow.current_step, flow.completed_steps, flow.skipped_steps),
  };
}

/** Mark step completed, advance current_step */
export async function completeStep(
  db: D1Database,
  tenantId: string,
  step: string,
): Promise<OnboardingStatus | null> {
  const row = await db
    .prepare('SELECT * FROM onboarding_flows WHERE tenant_id = ?')
    .bind(tenantId)
    .first<Record<string, unknown>>();
  if (!row) return null;

  const flow = parseFlow(row);
  if (!flow.completed_steps.includes(step)) flow.completed_steps.push(step);

  const allDone = ONBOARDING_STEPS.every(
    (s) => flow.completed_steps.includes(s) || flow.skipped_steps.includes(s),
  );
  const status: OnboardingFlow['status'] = allDone ? 'completed' : 'in_progress';
  const next = nextStep(step, flow.completed_steps, flow.skipped_steps) ?? step;

  await db
    .prepare(
      `UPDATE onboarding_flows
       SET current_step = ?, completed_steps = ?, status = ?, completed_at = ?
       WHERE tenant_id = ?`,
    )
    .bind(
      allDone ? step : next,
      JSON.stringify(flow.completed_steps),
      status,
      allDone ? new Date().toISOString() : null,
      tenantId,
    )
    .run();
  await logEvent(db, tenantId, step, 'completed');
  return getOnboardingStatus(db, tenantId);
}

/** Mark step skipped, advance current_step */
export async function skipStep(
  db: D1Database,
  tenantId: string,
  step: string,
): Promise<OnboardingStatus | null> {
  const row = await db
    .prepare('SELECT * FROM onboarding_flows WHERE tenant_id = ?')
    .bind(tenantId)
    .first<Record<string, unknown>>();
  if (!row) return null;

  const flow = parseFlow(row);
  if (!flow.skipped_steps.includes(step)) flow.skipped_steps.push(step);

  const next = nextStep(step, flow.completed_steps, flow.skipped_steps) ?? step;
  await db
    .prepare(
      `UPDATE onboarding_flows SET current_step = ?, skipped_steps = ? WHERE tenant_id = ?`,
    )
    .bind(next, JSON.stringify(flow.skipped_steps), tenantId)
    .run();
  await logEvent(db, tenantId, step, 'skipped');
  return getOnboardingStatus(db, tenantId);
}

/** Suggest next incomplete steps with reasons */
export async function getRecommendations(
  db: D1Database,
  tenantId: string,
): Promise<{ step: string; reason: string }[]> {
  const status = await getOnboardingStatus(db, tenantId);
  if (!status) return [];
  const done = new Set([...status.completed_steps, ...status.skipped_steps]);
  return ONBOARDING_STEPS.filter((s) => !done.has(s)).map((s) => ({
    step: s,
    reason: STEP_REASONS[s] ?? 'Complete this step',
  }));
}

// Seed defaults moved to onboarding-v2-seed-defaults.ts
export { autoSeedDefaults } from './onboarding-v2-seed-defaults';

/** Event history for tenant */
export async function getOnboardingEvents(
  db: D1Database,
  tenantId: string,
  limit = 50,
): Promise<Record<string, unknown>[]> {
  const { results } = await db
    .prepare(
      'SELECT * FROM onboarding_events WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?',
    )
    .bind(tenantId, limit)
    .all();
  return results as Record<string, unknown>[];
}

/** Reset flow to welcome step */
export async function resetOnboarding(db: D1Database, tenantId: string): Promise<OnboardingFlow> {
  await db
    .prepare(
      `UPDATE onboarding_flows
       SET current_step = 'welcome', completed_steps = '[]', skipped_steps = '[]',
           status = 'in_progress', completed_at = NULL, started_at = datetime('now')
       WHERE tenant_id = ?`,
    )
    .bind(tenantId)
    .run();
  await logEvent(db, tenantId, 'welcome', 'reset');

  const row = await db
    .prepare('SELECT * FROM onboarding_flows WHERE tenant_id = ?')
    .bind(tenantId)
    .first<Record<string, unknown>>();
  return parseFlow(row!);
}

// Admin functions moved to onboarding-v2-admin.ts
export { getCompletionRate, getDropoffAnalysis } from './onboarding-v2-admin';
