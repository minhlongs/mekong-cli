/**
 * Onboarding V2 Routes — wizard flow for tenant onboarding
 * GET  /status              current step + progress
 * POST /start               begin onboarding flow
 * POST /complete/:step      mark step done
 * POST /skip/:step          mark step skipped
 * GET  /recommendations     suggest next actions
 * POST /seed-defaults        auto-seed notification prefs, retention, SLOs
 * GET  /events              event history
 * POST /reset               restart flow
 * GET  /admin/completion-rate  (admin) % tenants completed
 * GET  /admin/dropoff          (admin) step abandon analysis
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  startOnboarding,
  getOnboardingStatus,
  completeStep,
  skipStep,
  getRecommendations,
  getOnboardingEvents,
  resetOnboarding,
} from '../services/onboarding-v2-service';
import { autoSeedDefaults } from '../services/onboarding-v2-seed-defaults';
import { getCompletionRate, getDropoffAnalysis } from '../services/onboarding-v2-admin';

export const app = new Hono<{ Bindings: Env }>();

// All routes require auth
app.use('/*', auth());

// ─── Admin guard ─────────────────────────────────────────────────────────────

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!key && key === c.env.ADMIN_API_KEY;
}

// ─── Tenant routes ───────────────────────────────────────────────────────────

app.get('/status', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const status = await getOnboardingStatus(c.env.DB, tenantId);
    if (!status) return json({ error: 'Onboarding not started', code: 'NOT_FOUND' }, { status: 404 });
    return json(status);
  } catch (e) {
    return json({ error: 'Failed to fetch status', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

app.post('/start', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const flow = await startOnboarding(c.env.DB, tenantId);
    return json(flow, { status: 201 });
  } catch (e) {
    return json({ error: 'Failed to start onboarding', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

app.post('/complete/:step', async (c) => {
  const { tenantId } = getTenant(c);
  const step = c.req.param('step');
  try {
    const status = await completeStep(c.env.DB, tenantId, step);
    if (!status) return json({ error: 'Onboarding flow not found', code: 'NOT_FOUND' }, { status: 404 });
    return json(status);
  } catch (e) {
    return json({ error: 'Failed to complete step', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

app.post('/skip/:step', async (c) => {
  const { tenantId } = getTenant(c);
  const step = c.req.param('step');
  try {
    const status = await skipStep(c.env.DB, tenantId, step);
    if (!status) return json({ error: 'Onboarding flow not found', code: 'NOT_FOUND' }, { status: 404 });
    return json(status);
  } catch (e) {
    return json({ error: 'Failed to skip step', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

app.get('/recommendations', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const recs = await getRecommendations(c.env.DB, tenantId);
    return json({ recommendations: recs });
  } catch (e) {
    return json({ error: 'Failed to get recommendations', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

app.post('/seed-defaults', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await autoSeedDefaults(c.env.DB, tenantId);
    return json(result);
  } catch (e) {
    return json({ error: 'Failed to seed defaults', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

app.get('/events', async (c) => {
  const { tenantId } = getTenant(c);
  const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10), 100);
  try {
    const events = await getOnboardingEvents(c.env.DB, tenantId, limit);
    return json({ events });
  } catch (e) {
    return json({ error: 'Failed to fetch events', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

app.post('/reset', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const flow = await resetOnboarding(c.env.DB, tenantId);
    return json(flow);
  } catch (e) {
    return json({ error: 'Failed to reset onboarding', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// ─── Admin routes ─────────────────────────────────────────────────────────────

app.get('/admin/completion-rate', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Admin access required', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const rate = await getCompletionRate(c.env.DB);
    return json(rate);
  } catch (e) {
    return json({ error: 'Failed to fetch completion rate', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

app.get('/admin/dropoff', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Admin access required', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const analysis = await getDropoffAnalysis(c.env.DB);
    return json({ steps: analysis });
  } catch (e) {
    return json({ error: 'Failed to fetch dropoff analysis', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

export { app as onboardingV2 };
