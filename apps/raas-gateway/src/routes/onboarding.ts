/**
 * Onboarding routes — guided activation checklist for new tenants
 * Goal: time-to-first-mission < 2 minutes
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const onboarding = new Hono<{ Bindings: Env }>();

const KNOWN_STEPS = ['signup_complete', 'first_mission', 'explore_templates', 'set_webhook', 'invite_referral'] as const;
type OnboardingStep = typeof KNOWN_STEPS[number];

interface OnboardingRow {
  id: string;
  tenant_id: string;
  steps_completed: string;
  current_step: number;
  completed_at: string | null;
}

const TIPS_CONTENT = {
  tips: [
    {
      id: 'first_mission',
      title: 'Submit your first mission',
      description: 'POST to /v1/missions with a goal. Simple missions cost 1 MCU.',
      example: { method: 'POST', url: '/v1/missions', body: { goal: 'Write a product description', complexity: 'simple' } },
    },
    {
      id: 'explore_templates',
      title: 'Browse mission templates',
      description: 'Pre-built templates by category to accelerate common workflows.',
      categories: ['marketing', 'engineering', 'sales', 'content', 'research'],
      url: '/v1/missions/templates',
    },
    {
      id: 'set_webhook',
      title: 'Set up a webhook',
      description: 'Receive real-time mission results via webhook instead of polling.',
      example: { method: 'PUT', url: '/v1/tenants/settings', body: { webhook_url: 'https://your-app.com/webhook/mekong' } },
    },
  ],
  quickstart: {
    steps: [
      '1. Sign up → receive 10 free MCU credits',
      '2. POST /v1/missions with your goal (costs 1 MCU)',
      '3. Poll GET /v1/missions/{id} or set webhook for results',
      '4. Browse /v1/missions/templates to automate workflows',
      '5. Invite a referral to earn bonus credits',
    ],
    docsUrl: 'https://mekong-raas.pages.dev/docs',
  },
};

/** Resolve which steps are actually done based on live DB state */
async function resolveSteps(env: Env, tenantId: string, saved: OnboardingStep[]): Promise<Record<OnboardingStep, boolean>> {
  const [missionRow, tenantRow] = await Promise.all([
    env.DB.prepare('SELECT COUNT(*) as c FROM missions WHERE tenant_id = ?').bind(tenantId).first<{ c: number }>(),
    env.DB.prepare('SELECT webhook_url FROM tenants WHERE id = ?').bind(tenantId).first<{ webhook_url: string | null }>(),
  ]);
  return {
    signup_complete: true,
    first_mission: (missionRow?.c ?? 0) > 0 || saved.includes('first_mission'),
    explore_templates: saved.includes('explore_templates'),
    set_webhook: !!tenantRow?.webhook_url || saved.includes('set_webhook'),
    invite_referral: saved.includes('invite_referral'),
  };
}

/** Fetch or auto-create onboarding_progress row for tenant */
async function getOrCreateRow(env: Env, tenantId: string): Promise<OnboardingRow> {
  const row = await env.DB.prepare('SELECT * FROM onboarding_progress WHERE tenant_id = ?')
    .bind(tenantId).first<OnboardingRow>();
  if (row) return row;

  const id = crypto.randomUUID();
  await env.DB.prepare(
    `INSERT INTO onboarding_progress (id, tenant_id, steps_completed, current_step) VALUES (?, ?, '[]', 0)`
  ).bind(id, tenantId).run();
  return { id, tenant_id: tenantId, steps_completed: '[]', current_step: 0, completed_at: null };
}

/** GET /v1/onboarding/checklist — return current checklist for authenticated tenant */
onboarding.get('/checklist', auth(), async (c) => {
  const tenant = getTenant(c);
  const row = await getOrCreateRow(c.env, tenant.tenantId);
  const saved: OnboardingStep[] = JSON.parse(row.steps_completed || '[]');
  const resolved = await resolveSteps(c.env, tenant.tenantId, saved);
  const checklist = KNOWN_STEPS.map((step, index) => ({ step, index, completed: resolved[step] }));

  return json({
    checklist,
    completedCount: checklist.filter((s) => s.completed).length,
    totalSteps: KNOWN_STEPS.length,
    fullyCompleted: !!row.completed_at,
    completedAt: row.completed_at,
    currentStep: row.current_step,
  });
});

/** POST /v1/onboarding/complete — mark a step completed; awards 5 credits when all done */
onboarding.post('/complete', auth(), async (c) => {
  const tenant = getTenant(c);

  let body: { step?: string };
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON body', code: 'BAD_REQUEST' }, { status: 400 });
  }

  const step = body.step as OnboardingStep;
  if (!step || !KNOWN_STEPS.includes(step)) {
    return json({ error: `Invalid step. Must be one of: ${KNOWN_STEPS.join(', ')}`, code: 'INVALID_STEP' }, { status: 400 });
  }

  const row = await getOrCreateRow(c.env, tenant.tenantId);
  const saved: OnboardingStep[] = JSON.parse(row.steps_completed || '[]');
  if (!saved.includes(step)) saved.push(step);

  const resolved = await resolveSteps(c.env, tenant.tenantId, saved);
  const allDone = KNOWN_STEPS.every((s) => resolved[s]);
  const isFirstCompletion = allDone && !row.completed_at;
  const completedAt = isFirstCompletion ? new Date().toISOString() : row.completed_at;

  await c.env.DB.prepare(
    `UPDATE onboarding_progress SET steps_completed = ?, current_step = ?, completed_at = ?, updated_at = datetime('now') WHERE tenant_id = ?`
  ).bind(JSON.stringify(saved), saved.length, completedAt, tenant.tenantId).run();

  if (isFirstCompletion) {
    await c.env.DB.prepare('UPDATE tenants SET balance = balance + 5, total_earned = total_earned + 5 WHERE id = ?')
      .bind(tenant.tenantId).run();
    await c.env.DB.prepare(
      `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at)
       VALUES (?, ?, 5, 'adjustment', 'Onboarding completion bonus', '{}', datetime('now'))`
    ).bind(crypto.randomUUID(), tenant.tenantId).run();
  }

  return json({
    success: true,
    checklist: KNOWN_STEPS.map((s, i) => ({ step: s, index: i, completed: resolved[s] })),
    completedCount: KNOWN_STEPS.filter((s) => resolved[s]).length,
    totalSteps: KNOWN_STEPS.length,
    fullyCompleted: allDone,
    bonusAwarded: isFirstCompletion ? 5 : 0,
  });
});

/** GET /v1/onboarding/tips — public quickstart content, no auth required */
onboarding.get('/tips', (c) => json(TIPS_CONTENT));
