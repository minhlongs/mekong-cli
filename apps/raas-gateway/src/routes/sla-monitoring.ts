/**
 * SLA Monitoring routes — uptime tracking and SLA compliance endpoints
 * Public: /sla/targets, /sla/status, /sla/uptime
 * Auth:   /sla/report
 * Admin:  /sla/breaches, /sla/history, /sla/check
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  getSLATiers,
  getSLATarget,
  getCurrentStatus,
  getUptimePercentage,
  getSLAReport,
  getSLABreaches,
  getUptimeHistory,
  recordUptimeCheck,
} from '../services/sla-monitoring-service';

export const slaMonitoring = new Hono<{ Bindings: Env }>();

/** Admin auth check — returns true if request is authorized as admin */
function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// GET /sla/targets — all SLA tier targets (public)
slaMonitoring.get('/targets', (c) => {
  return json({ targets: getSLATiers() });
});

// GET /sla/status — current platform operational status (public)
slaMonitoring.get('/status', async (c) => {
  try {
    const status = await getCurrentStatus(c.env.DB);
    return json(status);
  } catch {
    return json({ error: 'Failed to fetch status' }, { status: 500 });
  }
});

// GET /sla/uptime?days=30 — uptime percentage over window (public)
slaMonitoring.get('/uptime', async (c) => {
  const days = Math.min(Number(c.req.query('days') || 30), 90);
  try {
    const uptime = await getUptimePercentage(c.env.DB, days);
    return json({ period_days: days, ...uptime });
  } catch {
    return json({ error: 'Failed to fetch uptime' }, { status: 500 });
  }
});

// GET /sla/report?days=30 — SLA compliance report for tenant (auth required)
slaMonitoring.get('/report', auth(), async (c) => {
  const tenant = getTenant(c);
  const days = Math.min(Number(c.req.query('days') || 30), 90);
  try {
    // Derive tier from tenant data; default to 'starter' if unavailable
    const tenantRow = await c.env.DB.prepare(
      `SELECT plan FROM tenants WHERE id = ? LIMIT 1`
    ).bind(tenant.tenantId).first<{ plan: string }>();
    const tier = tenantRow?.plan ?? 'starter';

    // Validate tier exists, fall back to starter
    const target = getSLATarget(tier);
    const report = await getSLAReport(c.env.DB, tenant.tenantId, target.tier, days);
    return json(report);
  } catch {
    return json({ error: 'Failed to generate SLA report' }, { status: 500 });
  }
});

// GET /sla/breaches?days=30 — SLA breach history (admin only)
slaMonitoring.get('/breaches', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  const days = Math.min(Number(c.req.query('days') || 30), 365);
  try {
    const breaches = await getSLABreaches(c.env.DB, days);
    return json({ period_days: days, breaches });
  } catch {
    return json({ error: 'Failed to fetch breaches' }, { status: 500 });
  }
});

// GET /sla/history?days=7&limit=100 — uptime check history (admin only)
slaMonitoring.get('/history', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  const days = Math.min(Number(c.req.query('days') || 7), 90);
  const limit = Math.min(Number(c.req.query('limit') || 100), 500);
  try {
    const history = await getUptimeHistory(c.env.DB, days, limit);
    return json({ period_days: days, count: history.length, history });
  } catch {
    return json({ error: 'Failed to fetch history' }, { status: 500 });
  }
});

// POST /sla/check — record uptime check (admin only, for scheduled handler)
slaMonitoring.post('/check', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  try {
    const body = await c.req.json<{
      check_type?: string;
      status: 'up' | 'down' | 'degraded';
      latency_ms: number;
      details?: string;
    }>();

    if (!body.status || body.latency_ms == null) {
      return json({ error: 'status and latency_ms required' }, { status: 400 });
    }
    const validStatuses = ['up', 'down', 'degraded'];
    if (!validStatuses.includes(body.status)) {
      return json({ error: 'status must be up|down|degraded' }, { status: 400 });
    }

    await recordUptimeCheck(
      c.env.DB,
      body.check_type ?? 'api',
      body.status,
      body.latency_ms,
      body.details
    );
    return json({ recorded: true }, { status: 201 });
  } catch {
    return json({ error: 'Failed to record check' }, { status: 500 });
  }
});
