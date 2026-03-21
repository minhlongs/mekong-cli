/**
 * Sales tools routes — ROI calculator, demo sandbox, trial signup
 * Public routes: /tools/* (no auth)
 * Admin routes: /admin/sales/* (X-Admin-Key required)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { RoiCalculatorService } from '../services/roi-calculator-service';
import type { RoiInput } from '../services/roi-calculator-service';

export const salesTools = new Hono<{ Bindings: Env }>();

const roiService = new RoiCalculatorService();

// Admin auth middleware
const adminAuth = () => async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  }
  await next();
};

// ---------------------------------------------------------------------------
// Public: POST /tools/roi-calculator
// ---------------------------------------------------------------------------
salesTools.post('/tools/roi-calculator', async (c) => {
  const body = await c.req.json().catch(() => ({})) as Partial<RoiInput>;

  const { team_size, missions_per_month, current_monthly_cost, avg_mission_time_hours } = body;

  if (!team_size || !missions_per_month || current_monthly_cost === undefined) {
    return json({
      error: 'team_size, missions_per_month, and current_monthly_cost are required',
      code: 'INVALID_INPUT',
    }, { status: 400 });
  }

  const result = roiService.calculate({
    team_size: Number(team_size),
    missions_per_month: Number(missions_per_month),
    current_monthly_cost: Number(current_monthly_cost),
    avg_mission_time_hours: avg_mission_time_hours ? Number(avg_mission_time_hours) : undefined,
  });

  return json(result);
});

// ---------------------------------------------------------------------------
// Public: POST /tools/demo/request — provision 2-hour demo sandbox
// ---------------------------------------------------------------------------
salesTools.post('/tools/demo/request', async (c) => {
  const body = await c.req.json().catch(() => ({})) as { email?: string; company_name?: string };

  const id = crypto.randomUUID();
  const demoTenantId = `demo_${crypto.randomUUID().slice(0, 8)}`;
  const demoApiKey = `demo_key_${crypto.randomUUID()}`;
  // Expires in 2 hours
  const expiresAt = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString();

  await c.env.DB.prepare(
    `INSERT INTO demo_sandboxes (id, email, demo_tenant_id, demo_api_key, expires_at, status, created_at)
     VALUES (?, ?, ?, ?, ?, 'active', datetime('now'))`
  ).bind(id, body.email ?? null, demoTenantId, demoApiKey, expiresAt).run();

  return json({
    demo_id: id,
    demo_tenant_id: demoTenantId,
    demo_api_key: demoApiKey,
    expires_at: expiresAt,
    message: 'Demo sandbox active for 2 hours. Use demo_api_key as your X-API-Key.',
  }, { status: 201 });
});

// ---------------------------------------------------------------------------
// Public: POST /tools/trial/signup — start 14-day trial
// ---------------------------------------------------------------------------
salesTools.post('/tools/trial/signup', async (c) => {
  const body = await c.req.json().catch(() => ({})) as {
    email?: string;
    company_name?: string;
    tier?: string;
  };

  if (!body.email) {
    return json({ error: 'email is required', code: 'INVALID_INPUT' }, { status: 400 });
  }

  // Prevent duplicate active trials
  const existing = await c.env.DB.prepare(
    `SELECT id FROM trial_signups WHERE email = ? AND status = 'active'`
  ).bind(body.email).first<{ id: string }>();

  if (existing) {
    return json({ error: 'Active trial already exists for this email', code: 'DUPLICATE_TRIAL' }, { status: 409 });
  }

  const validTiers = ['starter', 'pro', 'agency', 'master', 'enterprise'];
  const tier = validTiers.includes(body.tier ?? '') ? body.tier! : 'starter';

  const id = crypto.randomUUID();
  const trialEnd = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString();

  await c.env.DB.prepare(
    `INSERT INTO trial_signups (id, email, company_name, trial_tier, trial_days, trial_start, trial_end, status, created_at)
     VALUES (?, ?, ?, ?, 14, datetime('now'), ?, 'active', datetime('now'))`
  ).bind(id, body.email, body.company_name ?? null, tier, trialEnd).run();

  return json({
    trial_id: id,
    email: body.email,
    tier,
    trial_days: 14,
    trial_end: trialEnd,
    message: 'Trial started. You have 14 days of full access.',
  }, { status: 201 });
});

// ---------------------------------------------------------------------------
// Admin: GET /admin/sales/demos — list active demo sandboxes
// ---------------------------------------------------------------------------
salesTools.get('/admin/sales/demos', adminAuth(), async (c) => {
  const rows = await c.env.DB.prepare(
    `SELECT id, email, demo_tenant_id, expires_at, status, converted_tenant_id, created_at
     FROM demo_sandboxes WHERE status = 'active' ORDER BY created_at DESC`
  ).all();

  return json({ demos: rows.results, total: rows.results.length });
});

// ---------------------------------------------------------------------------
// Admin: GET /admin/sales/trials — list trial signups (query: status)
// ---------------------------------------------------------------------------
salesTools.get('/admin/sales/trials', adminAuth(), async (c) => {
  const status = c.req.query('status') ?? 'active';
  const validStatuses = ['active', 'expired', 'converted', 'cancelled'];
  const safeStatus = validStatuses.includes(status) ? status : 'active';

  const rows = await c.env.DB.prepare(
    `SELECT id, email, company_name, trial_tier, trial_start, trial_end, status, converted_at, created_at
     FROM trial_signups WHERE status = ? ORDER BY created_at DESC`
  ).bind(safeStatus).all();

  return json({ trials: rows.results, total: rows.results.length, status: safeStatus });
});

// ---------------------------------------------------------------------------
// Admin: GET /admin/sales/trials/metrics — trial conversion metrics
// ---------------------------------------------------------------------------
salesTools.get('/admin/sales/trials/metrics', adminAuth(), async (c) => {
  const [counts, byTier] = await Promise.all([
    c.env.DB.prepare(
      `SELECT status, COUNT(*) as count FROM trial_signups GROUP BY status`
    ).all<{ status: string; count: number }>(),

    c.env.DB.prepare(
      `SELECT trial_tier, COUNT(*) as total,
       SUM(CASE WHEN status='converted' THEN 1 ELSE 0 END) as converted
       FROM trial_signups GROUP BY trial_tier`
    ).all<{ trial_tier: string; total: number; converted: number }>(),
  ]);

  const statusMap: Record<string, number> = {};
  for (const row of counts.results) statusMap[row.status] = row.count;

  const converted = statusMap['converted'] ?? 0;
  const expired = statusMap['expired'] ?? 0;
  const conversionRate = (converted + expired) > 0
    ? Math.round((converted / (converted + expired)) * 100)
    : 0;

  return json({
    by_status: statusMap,
    conversion_rate_pct: conversionRate,
    by_tier: byTier.results,
  });
});
