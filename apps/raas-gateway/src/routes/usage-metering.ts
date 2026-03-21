/**
 * Usage metering routes — current usage, history, quotas, overage billing
 *
 * All routes require auth middleware.
 * Admin routes additionally require ADMIN_API_KEY header.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const usageMetering = new Hono<{ Bindings: Env }>();

// All routes require auth
usageMetering.use('/*', auth());

/** Get today key: YYYY-MM-DD */
function todayKey(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Get current month key: YYYY-MM */
function monthKey(): string {
  return new Date().toISOString().slice(0, 7);
}

/**
 * GET /v1/usage/current — daily + monthly usage counts from KV
 */
usageMetering.get('/current', async (c) => {
  const tenant = getTenant(c);
  const { tenantId } = tenant;
  const kv = c.env.RATE_LIMIT_KV;

  const [dailyRaw, monthlyRaw, quota] = await Promise.all([
    kv.get(`usage:${tenantId}:${todayKey()}`),
    kv.get(`usage:${tenantId}:${monthKey()}`),
    c.env.DB
      .prepare('SELECT daily_limit, monthly_limit, overage_rate_cents FROM usage_quotas WHERE tenant_id = ?')
      .bind(tenantId)
      .first<{ daily_limit: number; monthly_limit: number; overage_rate_cents: number }>()
      .catch(() => null),
  ]);

  const daily = parseInt(dailyRaw ?? '0', 10) || 0;
  const monthly = parseInt(monthlyRaw ?? '0', 10) || 0;
  const dailyLimit = quota?.daily_limit ?? 1000;
  const monthlyLimit = quota?.monthly_limit ?? 25000;

  return json({
    tenantId,
    period: { date: todayKey(), month: monthKey() },
    usage: { daily, monthly },
    limits: { daily: dailyLimit, monthly: monthlyLimit },
    overage: {
      daily: Math.max(0, daily - dailyLimit),
      monthly: Math.max(0, monthly - monthlyLimit),
    },
  });
});

/**
 * GET /v1/usage/history?days=30 — paginated usage records from D1
 */
usageMetering.get('/history', async (c) => {
  const tenant = getTenant(c);
  const days = Math.min(Math.max(parseInt(c.req.query('days') ?? '30', 10), 1), 90);
  const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '100', 10), 1), 500);
  const offset = Math.max(0, parseInt(c.req.query('offset') ?? '0', 10));

  const cutoff = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

  const [rows, countRow] = await Promise.all([
    c.env.DB
      .prepare(
        `SELECT id, endpoint, method, status_code, credits_consumed, recorded_at
         FROM usage_records
         WHERE tenant_id = ? AND recorded_at >= ?
         ORDER BY recorded_at DESC
         LIMIT ? OFFSET ?`
      )
      .bind(tenant.tenantId, cutoff, limit, offset)
      .all<{ id: string; endpoint: string; method: string; status_code: number; credits_consumed: number; recorded_at: string }>(),
    c.env.DB
      .prepare('SELECT COUNT(*) as total FROM usage_records WHERE tenant_id = ? AND recorded_at >= ?')
      .bind(tenant.tenantId, cutoff)
      .first<{ total: number }>(),
  ]);

  return json({
    tenantId: tenant.tenantId,
    days,
    records: rows.results ?? [],
    pagination: { limit, offset, total: countRow?.total ?? 0 },
  });
});

/**
 * POST /v1/usage/quotas — set custom quotas (admin only, requires ADMIN_API_KEY header)
 */
usageMetering.post('/quotas', async (c) => {
  const adminKey = c.req.header('X-Admin-API-Key') ?? c.req.header('X-Api-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Admin API key required', code: 'FORBIDDEN' }, { status: 403 });
  }

  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const targetTenantId = (body.tenant_id as string)?.trim();
  const dailyLimit = typeof body.daily_limit === 'number' ? body.daily_limit : null;
  const monthlyLimit = typeof body.monthly_limit === 'number' ? body.monthly_limit : null;
  const overageRateCents = typeof body.overage_rate_cents === 'number' ? body.overage_rate_cents : null;

  if (!targetTenantId) {
    return json({ error: 'tenant_id required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }

  await c.env.DB
    .prepare(
      `INSERT INTO usage_quotas (tenant_id, daily_limit, monthly_limit, overage_rate_cents)
       VALUES (?, ?, ?, ?)
       ON CONFLICT(tenant_id) DO UPDATE SET
         daily_limit = COALESCE(excluded.daily_limit, daily_limit),
         monthly_limit = COALESCE(excluded.monthly_limit, monthly_limit),
         overage_rate_cents = COALESCE(excluded.overage_rate_cents, overage_rate_cents)`
    )
    .bind(targetTenantId, dailyLimit ?? 1000, monthlyLimit ?? 25000, overageRateCents ?? 1)
    .run();

  return json({ updated: true, tenantId: targetTenantId, daily_limit: dailyLimit, monthly_limit: monthlyLimit, overage_rate_cents: overageRateCents });
});

/**
 * GET /v1/usage/overage — overage charges for current billing period
 */
usageMetering.get('/overage', async (c) => {
  const tenant = getTenant(c);
  const { tenantId } = tenant;
  const kv = c.env.RATE_LIMIT_KV;

  const [monthlyRaw, quota] = await Promise.all([
    kv.get(`usage:${tenantId}:${monthKey()}`),
    c.env.DB
      .prepare('SELECT monthly_limit, overage_rate_cents FROM usage_quotas WHERE tenant_id = ?')
      .bind(tenantId)
      .first<{ monthly_limit: number; overage_rate_cents: number }>()
      .catch(() => null),
  ]);

  const monthly = parseInt(monthlyRaw ?? '0', 10) || 0;
  const monthlyLimit = quota?.monthly_limit ?? 25000;
  const overageRateCents = quota?.overage_rate_cents ?? 1;
  const overageRequests = Math.max(0, monthly - monthlyLimit);
  const overageChargeCents = overageRequests * overageRateCents;

  return json({
    tenantId,
    period: monthKey(),
    usage: monthly,
    limit: monthlyLimit,
    overageRequests,
    overageRateCents,
    overageChargeCents,
    overageChargeDollars: (overageChargeCents / 100).toFixed(2),
  });
});
