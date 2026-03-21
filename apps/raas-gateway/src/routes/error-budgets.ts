/**
 * Error Budget routes — SLO definitions, SLI measurements, budget tracking, and alerts
 * All routes require tenant auth.
 * Mount order: /summary, /alerts, /seed BEFORE /slos/:id to prevent route shadowing
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createSlo,
  getSlos,
  updateSlo,
  deleteSlo,
  recordMeasurement,
  calculateErrorBudget,
  getErrorBudgetSummary,
  checkAndAlert,
  getAlerts,
  acknowledgeAlert,
  seedDefaultSlos,
} from '../services/error-budget-service';

const app = new Hono<{ Bindings: Env }>();
app.use('/*', auth());

// GET /error-budgets/slos — list all SLOs for tenant
app.get('/slos', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const slos = await getSlos(c.env.DB, tenantId);
    return json({ slos });
  } catch {
    return json({ error: 'Failed to fetch SLOs' }, { status: 500 });
  }
});

// POST /error-budgets/slos — create a new SLO
app.post('/slos', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json<{ name: string; slo_type: string; target_value: number; window_days?: number }>();
    if (!body.name || !body.slo_type || body.target_value == null) {
      return json({ error: 'name, slo_type, and target_value are required' }, { status: 400 });
    }
    const slo = await createSlo(c.env.DB, tenantId, body.name, body.slo_type, body.target_value, body.window_days ?? 30);
    return json({ slo }, { status: 201 });
  } catch {
    return json({ error: 'Failed to create SLO' }, { status: 500 });
  }
});

// GET /error-budgets/summary — error budget status for all active SLOs
app.get('/summary', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const summary = await getErrorBudgetSummary(c.env.DB, tenantId);
    const healthy = summary.filter((s) => s.is_healthy).length;
    return json({ total: summary.length, healthy, at_risk: summary.length - healthy, slos: summary });
  } catch {
    return json({ error: 'Failed to fetch summary' }, { status: 500 });
  }
});

// GET /error-budgets/alerts — list alerts (?unacknowledged=true)
app.get('/alerts', async (c) => {
  const { tenantId } = getTenant(c);
  const unackOnly = c.req.query('unacknowledged') === 'true';
  try {
    const alerts = await getAlerts(c.env.DB, tenantId, unackOnly);
    return json({ alerts });
  } catch {
    return json({ error: 'Failed to fetch alerts' }, { status: 500 });
  }
});

// POST /error-budgets/alerts/:id/ack — acknowledge an alert
app.post('/alerts/:id/ack', async (c) => {
  try {
    await acknowledgeAlert(c.env.DB, c.req.param('id'));
    return json({ acknowledged: true });
  } catch {
    return json({ error: 'Failed to acknowledge alert' }, { status: 500 });
  }
});

// POST /error-budgets/seed — seed default SLOs for tenant
app.post('/seed', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const slos = await seedDefaultSlos(c.env.DB, tenantId);
    return json({ seeded: slos.length, slos }, { status: 201 });
  } catch {
    return json({ error: 'Failed to seed SLOs' }, { status: 500 });
  }
});

// PUT /error-budgets/slos/:id — update SLO
app.put('/slos/:id', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json<{ name?: string; target_value?: number; window_days?: number; is_active?: number }>();
    await updateSlo(c.env.DB, tenantId, c.req.param('id'), body);
    return json({ updated: true });
  } catch {
    return json({ error: 'Failed to update SLO' }, { status: 500 });
  }
});

// DELETE /error-budgets/slos/:id — delete SLO
app.delete('/slos/:id', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    await deleteSlo(c.env.DB, tenantId, c.req.param('id'));
    return json({ deleted: true });
  } catch {
    return json({ error: 'Failed to delete SLO' }, { status: 500 });
  }
});

// GET /error-budgets/slos/:id/budget — single SLO budget details
app.get('/slos/:id/budget', async (c) => {
  try {
    const budget = await calculateErrorBudget(c.env.DB, c.req.param('id'));
    if (!budget) return json({ error: 'SLO not found' }, { status: 404 });
    // Also trigger alert check on each budget fetch
    await checkAndAlert(c.env.DB, c.req.param('id'));
    return json({ budget });
  } catch {
    return json({ error: 'Failed to calculate budget' }, { status: 500 });
  }
});

// POST /error-budgets/slos/:id/measure — record SLI measurement
app.post('/slos/:id/measure', async (c) => {
  try {
    const body = await c.req.json<{ measured_value: number; good_events?: number; total_events?: number }>();
    if (body.measured_value == null) {
      return json({ error: 'measured_value is required' }, { status: 400 });
    }
    await recordMeasurement(c.env.DB, c.req.param('id'), body.measured_value, body.good_events ?? 0, body.total_events ?? 0);
    await checkAndAlert(c.env.DB, c.req.param('id'));
    return json({ recorded: true }, { status: 201 });
  } catch {
    return json({ error: 'Failed to record measurement' }, { status: 500 });
  }
});

export const errorBudgets = app;
