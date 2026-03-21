/**
 * Suspension routes — tenant account status + admin suspension management
 * /v1/account/status, /v1/account/reactivate, /admin/suspensions/*
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { TenantSuspensionService } from '../services/tenant-suspension-service';

// ── Tenant-facing routes (/v1/account) ──────────────────────────────────────

export const accountSuspension = new Hono<{ Bindings: Env }>();

/**
 * GET /v1/account/status — check if the authenticated tenant is suspended
 */
accountSuspension.get('/status', auth(), async (c) => {
  const tenant = getTenant(c);
  const svc = new TenantSuspensionService(c.env);

  const suspension = await svc.isSuspended(tenant.tenantId);
  if (!suspension) {
    return json({ suspended: false });
  }

  const inGrace = suspension.grace_period_ends
    ? new Date(suspension.grace_period_ends) > new Date()
    : false;

  return json({
    suspended: true,
    reason: suspension.reason,
    suspended_at: suspension.suspended_at,
    grace_period_ends: suspension.grace_period_ends,
    in_grace_period: inGrace,
    auto_resume_on_payment: suspension.auto_resume_on_payment === 1,
  });
});

/**
 * POST /v1/account/reactivate — trigger a payment retry for the suspended account
 */
accountSuspension.post('/reactivate', auth(), async (c) => {
  const tenant = getTenant(c);
  const svc = new TenantSuspensionService(c.env);

  const suspension = await svc.isSuspended(tenant.tenantId);
  if (!suspension) {
    return json({ error: 'Account is not suspended' }, { status: 400 });
  }

  const history = await svc.getRetryHistory(tenant.tenantId);
  const nextAttempt = history.length + 1;
  const retry = await svc.scheduleRetry(tenant.tenantId, nextAttempt);

  return json({
    queued: true,
    attempt_number: retry.attempt_number,
    next_retry_at: retry.next_retry_at,
  });
});

// ── Admin routes (/admin/suspensions) ───────────────────────────────────────

export const adminSuspensions = new Hono<{ Bindings: Env }>();

// Admin auth guard
adminSuspensions.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  await next();
});

/**
 * GET /admin/suspensions — list all currently suspended tenants
 */
adminSuspensions.get('/', async (c) => {
  const { results } = await c.env.DB.prepare(
    `SELECT s.*, t.name as tenant_name
     FROM tenant_suspensions s
     LEFT JOIN tenants t ON t.id = s.tenant_id
     ORDER BY s.suspended_at DESC
     LIMIT 100`
  ).all();
  return json({ suspensions: results, count: results.length });
});

/**
 * POST /admin/suspensions — suspend a tenant by ID
 * Body: { tenant_id, reason, grace_days? }
 */
adminSuspensions.post('/', async (c) => {
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const { tenant_id, reason, grace_days } = body as {
    tenant_id?: string;
    reason?: string;
    grace_days?: number;
  };

  if (!tenant_id || !reason) {
    return json({ error: 'tenant_id and reason are required' }, { status: 400 });
  }

  const tenant = await c.env.DB.prepare(
    'SELECT id FROM tenants WHERE id = ?'
  ).bind(tenant_id).first();

  if (!tenant) {
    return json({ error: 'Tenant not found' }, { status: 404 });
  }

  const svc = new TenantSuspensionService(c.env);
  const suspension = await svc.suspend(tenant_id, reason, grace_days, 'admin');

  return json({ suspended: true, suspension }, { status: 201 });
});

/**
 * DELETE /admin/suspensions/:tenantId — resume a suspended tenant
 */
adminSuspensions.delete('/:tenantId', async (c) => {
  const tenantId = c.req.param('tenantId');
  const svc = new TenantSuspensionService(c.env);

  const removed = await svc.resume(tenantId);
  if (!removed) {
    return json({ error: 'Suspension not found' }, { status: 404 });
  }
  return json({ resumed: true, tenant_id: tenantId });
});
