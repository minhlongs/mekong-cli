/**
 * Usage Alerts routes — alert rules, budget controls, and spending limit enforcement
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createAlertRule,
  listAlertRules,
  updateAlertRule,
  deleteAlertRule,
  getAlertHistory,
  setBudgetConfig,
  getBudgetConfig,
  checkBudgetLimit,
  getAdminAlertOverview,
} from '../services/usage-alerts-service';

export const usageAlerts = new Hono<{ Bindings: Env }>();

/**
 * GET /rules — list tenant's alert rules
 */
usageAlerts.get('/rules', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const rules = await listAlertRules(c.env.DB, tenantId);
    return json({ rules });
  } catch {
    return json({ error: 'Failed to fetch alert rules' }, { status: 500 });
  }
});

/**
 * POST /rules — create a new alert rule
 * Body: { rule_type, threshold_value, action, channel }
 */
usageAlerts.post('/rules', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { rule_type, threshold_value, action, channel } = body;
  if (!rule_type || threshold_value === undefined) {
    return json({ error: 'rule_type and threshold_value are required' }, { status: 400 });
  }
  const validTypes = ['credits_threshold', 'daily_limit', 'monthly_limit', 'rate_spike'];
  if (!validTypes.includes(String(rule_type))) {
    return json({ error: `rule_type must be one of: ${validTypes.join(', ')}` }, { status: 400 });
  }

  try {
    const rule = await createAlertRule(
      c.env.DB, tenantId,
      String(rule_type),
      Number(threshold_value),
      action ? String(action) : 'notify',
      channel ? String(channel) : 'email'
    );
    return json({ rule }, { status: 201 });
  } catch {
    return json({ error: 'Failed to create alert rule' }, { status: 500 });
  }
});

/**
 * PUT /rules/:ruleId — update an existing alert rule
 * Body: { threshold_value?, action?, channel?, is_active? }
 */
usageAlerts.put('/rules/:ruleId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const ruleId = c.req.param('ruleId');
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const updates: Record<string, unknown> = {};
  if (body.threshold_value !== undefined) updates.thresholdValue = Number(body.threshold_value);
  if (body.action !== undefined) updates.action = String(body.action);
  if (body.channel !== undefined) updates.channel = String(body.channel);
  if (body.is_active !== undefined) updates.isActive = body.is_active ? 1 : 0;

  try {
    const rule = await updateAlertRule(c.env.DB, tenantId, ruleId, updates);
    if (!rule) return json({ error: 'Alert rule not found' }, { status: 404 });
    return json({ rule });
  } catch {
    return json({ error: 'Failed to update alert rule' }, { status: 500 });
  }
});

/**
 * DELETE /rules/:ruleId — delete an alert rule
 */
usageAlerts.delete('/rules/:ruleId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const ruleId = c.req.param('ruleId');
  try {
    const deleted = await deleteAlertRule(c.env.DB, tenantId, ruleId);
    if (!deleted) return json({ error: 'Alert rule not found' }, { status: 404 });
    return json({ success: true, id: ruleId });
  } catch {
    return json({ error: 'Failed to delete alert rule' }, { status: 500 });
  }
});

/**
 * GET /history — alert trigger history
 * Query: ?limit=50
 */
usageAlerts.get('/history', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
  try {
    const history = await getAlertHistory(c.env.DB, tenantId, limit);
    return json({ history });
  } catch {
    return json({ error: 'Failed to fetch alert history' }, { status: 500 });
  }
});

/**
 * GET /budget — get tenant's budget config
 */
usageAlerts.get('/budget', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const budget = await getBudgetConfig(c.env.DB, tenantId);
    return json({ budget });
  } catch {
    return json({ error: 'Failed to fetch budget config' }, { status: 500 });
  }
});

/**
 * PUT /budget — set budget limits
 * Body: { monthly_budget?, daily_budget?, hard_limit? }
 */
usageAlerts.put('/budget', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const config: Record<string, unknown> = {};
  if (body.monthly_budget !== undefined) config.monthlyBudget = Number(body.monthly_budget);
  if (body.daily_budget !== undefined) config.dailyBudget = Number(body.daily_budget);
  if (body.hard_limit !== undefined) config.hardLimit = body.hard_limit ? 1 : 0;

  try {
    const budget = await setBudgetConfig(c.env.DB, tenantId, config);
    return json({ budget });
  } catch {
    return json({ error: 'Failed to update budget config' }, { status: 500 });
  }
});

/**
 * POST /check — check if a request is within budget
 * Body: { credits }
 */
usageAlerts.post('/check', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const credits = Number(body.credits);
  if (!credits || credits <= 0) {
    return json({ error: 'credits must be a positive number' }, { status: 400 });
  }

  try {
    const result = await checkBudgetLimit(c.env.DB, tenantId, credits);
    const status = result.hardBlock ? 402 : 200;
    return json(result, { status });
  } catch {
    return json({ error: 'Failed to check budget limit' }, { status: 500 });
  }
});

/**
 * GET /admin/overview — admin: most triggered rules, budget utilization
 * Requires X-Admin-Key header
 */
usageAlerts.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden' }, { status: 403 });
  }
  try {
    const overview = await getAdminAlertOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to fetch admin overview' }, { status: 500 });
  }
});
