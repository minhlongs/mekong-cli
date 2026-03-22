/**
 * Mission Quality Gates routes
 * Auth: GET /gates, POST /gates, GET /evaluations
 * Admin: GET /admin/overview (X-Admin-Key, 403 on mismatch)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionQualityGatesService } from '../services/mission-quality-gates';

const app = new Hono<{ Bindings: Env }>();

// --- Authenticated tenant routes ---

app.use('/gates', auth());
app.use('/gates/*', auth());
app.use('/evaluations', auth());

/**
 * GET /gates — List active quality gates for authenticated tenant
 */
app.get('/gates', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const gates = await missionQualityGatesService.listGates(c.env.DB, tenantId);
    return c.json({ success: true, data: gates, total: gates.length });
  } catch (err) {
    console.error('[missionQualityGates GET /gates] error:', err);
    return c.json({ success: false, error: 'Failed to list quality gates' }, 500);
  }
});

/**
 * POST /gates — Create a new quality gate for authenticated tenant
 * Body: { gate_name: string, criteria_json: string, is_blocking?: 0|1 }
 */
app.post('/gates', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({}));

    const gateName = (body.gate_name ?? '').trim();
    if (!gateName) {
      return c.json({ success: false, error: 'gate_name is required' }, 400);
    }

    const criteriaJson = body.criteria_json;
    if (!criteriaJson || typeof criteriaJson !== 'string') {
      return c.json({ success: false, error: 'criteria_json is required and must be a string' }, 400);
    }

    // Validate criteria_json is parseable JSON
    try {
      JSON.parse(criteriaJson);
    } catch {
      return c.json({ success: false, error: 'criteria_json must be valid JSON' }, 400);
    }

    const isBlocking = body.is_blocking === 0 ? 0 : 1;

    const gate = await missionQualityGatesService.createGate(
      c.env.DB,
      tenantId,
      gateName,
      criteriaJson,
      isBlocking
    );
    return c.json({ success: true, data: gate }, 201);
  } catch (err) {
    console.error('[missionQualityGates POST /gates] error:', err);
    return c.json({ success: false, error: 'Failed to create quality gate' }, 500);
  }
});

/**
 * GET /evaluations — List gate evaluations for authenticated tenant
 * Optional query param: mission_id
 */
app.get('/evaluations', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const missionId = c.req.query('mission_id')?.trim() || undefined;
    const evals = await missionQualityGatesService.getEvaluations(c.env.DB, tenantId, missionId);
    return c.json({ success: true, data: evals, total: evals.length });
  } catch (err) {
    console.error('[missionQualityGates GET /evaluations] error:', err);
    return c.json({ success: false, error: 'Failed to fetch evaluations' }, 500);
  }
});

// --- Admin routes ---

/**
 * GET /admin/overview — Pass/fail rates across all tenants
 * Protected by X-Admin-Key header; returns 403 on mismatch
 */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const overview = await missionQualityGatesService.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview, total: overview.length });
  } catch (err) {
    console.error('[missionQualityGates GET /admin/overview] error:', err);
    return c.json({ success: false, error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as missionQualityGates };
