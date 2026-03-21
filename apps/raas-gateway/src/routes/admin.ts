/**
 * Admin routes — stats/dashboard endpoints protected by X-Admin-Key header
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';

export const admin = new Hono<{ Bindings: Env }>();

// Simple admin auth via X-Admin-Key header
const adminAuth = () => async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  await next();
};

admin.use('/*', adminAuth());

// GET /admin/stats — Overview dashboard
admin.get('/stats', async (c) => {
  const [tenants, missions, credits, daily, tiers, recentSignups] = await Promise.all([
    c.env.DB.prepare('SELECT COUNT(*) as total, SUM(CASE WHEN active=1 THEN 1 ELSE 0 END) as active FROM tenants').first(),
    c.env.DB.prepare(`SELECT COUNT(*) as total,
      SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
      SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
      SUM(CASE WHEN status='queued' THEN 1 ELSE 0 END) as queued
      FROM missions`).first(),
    c.env.DB.prepare('SELECT COALESCE(SUM(balance),0) as totalBalance, COALESCE(SUM(total_earned),0) as totalEarned, COALESCE(SUM(total_spent),0) as totalSpent FROM tenants').first(),
    c.env.DB.prepare(`SELECT date(created_at) as day, COUNT(*) as signups
      FROM tenants WHERE created_at >= datetime('now', '-30 days')
      GROUP BY date(created_at) ORDER BY day DESC`).all(),
    c.env.DB.prepare('SELECT tier, COUNT(*) as count FROM tenants GROUP BY tier').all(),
    c.env.DB.prepare(`SELECT name, email, tier, balance, created_at FROM tenants
      ORDER BY created_at DESC LIMIT 10`).all(),
  ]);

  return json({
    tenants,
    missions,
    credits,
    dailySignups: daily.results,
    tierDistribution: tiers.results,
    recentSignups: recentSignups.results,
  });
});

// GET /admin/revenue — Revenue breakdown by transaction type
admin.get('/revenue', async (c) => {
  const [purchases, subscriptions, byType] = await Promise.all([
    c.env.DB.prepare(`SELECT COUNT(*) as count, COALESCE(SUM(amount),0) as total
      FROM credit_transactions WHERE type = 'purchase'`).first(),
    c.env.DB.prepare(`SELECT status, COUNT(*) as count FROM subscriptions GROUP BY status`).all(),
    c.env.DB.prepare(`SELECT type, COUNT(*) as count, COALESCE(SUM(amount),0) as total
      FROM credit_transactions GROUP BY type`).all(),
  ]);

  return json({ purchases, subscriptions: subscriptions.results, transactionsByType: byType.results });
});

// GET /admin/revenue/daily — Last 30 days daily revenue aggregated
admin.get('/revenue/daily', async (c) => {
  const daily = await c.env.DB.prepare(
    `SELECT date(created_at) as day,
            COUNT(*) as transactions,
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as credits_added,
            SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as credits_spent
     FROM credit_transactions
     WHERE created_at >= datetime('now', '-30 days')
     GROUP BY date(created_at) ORDER BY day DESC`
  ).all();
  return json({ daily: daily.results });
});

// GET /admin/revenue/mrr — Current MRR and ARR estimate by tier
admin.get('/revenue/mrr', async (c) => {
  const tiers = await c.env.DB.prepare(
    `SELECT tier, COUNT(*) as count FROM tenants WHERE active = 1 GROUP BY tier`
  ).all();

  const prices: Record<string, number> = {
    free: 0,
    starter: 29,
    pro: 99,
    agency: 199,
    master: 399,
  };

  let mrr = 0;
  const breakdown: Array<{ tier: string; count: number; mrr: number }> = [];

  for (const row of tiers.results as any[]) {
    const tierMrr = (prices[row.tier] || 0) * row.count;
    mrr += tierMrr;
    breakdown.push({ tier: row.tier, count: row.count, mrr: tierMrr });
  }

  return json({
    mrr,
    arr: mrr * 12,
    breakdown,
    timestamp: new Date().toISOString(),
  });
});

// GET /admin/revenue/churn — Tenants who deactivated this month
admin.get('/revenue/churn', async (c) => {
  const [churned, total] = await Promise.all([
    c.env.DB.prepare(
      `SELECT COUNT(*) as count FROM tenants
       WHERE active = 0 AND updated_at >= datetime('now', 'start of month')`
    ).first(),
    c.env.DB.prepare('SELECT COUNT(*) as count FROM tenants WHERE active = 1').first(),
  ]);

  const churnedCount = (churned as any)?.count || 0;
  const totalCount = (total as any)?.count || 0;

  return json({
    churned: churnedCount,
    totalActive: totalCount,
    churnRate: totalCount > 0
      ? ((churnedCount / totalCount) * 100).toFixed(2) + '%'
      : '0%',
  });
});

// GET /admin/rate-limits/:tenantId — Rate limit status for a specific tenant
admin.get('/rate-limits/:tenantId', async (c) => {
  const tenantId = c.req.param('tenantId');
  const minute = Math.floor(Date.now() / 60000);
  const key = `rl:${tenantId}:${minute}`;

  const [current, tenant] = await Promise.all([
    c.env.RATE_LIMIT_KV.get(key),
    c.env.DB.prepare('SELECT tier FROM tenants WHERE id = ?')
      .bind(tenantId)
      .first<{ tier: string }>(),
  ]);

  const limits: Record<string, number> = {
    free: 10,
    starter: 30,
    pro: 60,
    agency: 120,
    master: 300,
    enterprise: 1000,
  };

  const tier = tenant?.tier || 'free';
  const limit = limits[tier] || 10;
  const used = parseInt(current || '0');

  return json({
    tenantId,
    tier,
    currentMinute: used,
    limit,
    remaining: Math.max(0, limit - used),
    resetsAt: new Date((minute + 1) * 60000).toISOString(),
  });
});

// GET /admin/errors — Recent failed missions (proxy for error log)
admin.get('/errors', async (c) => {
  const errors = await c.env.DB.prepare(
    `SELECT id, tenant_id, goal, status, error, updated_at
     FROM missions WHERE status = 'failed'
     ORDER BY updated_at DESC LIMIT 50`
  ).all();
  return json({ errors: errors.results, total: errors.results.length });
});

// POST /admin/coupons — create a new promotional coupon code
admin.post('/coupons', async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const code = body.code?.trim()?.toUpperCase();
  const bonusCredits = parseInt(body.bonus_credits || '0');
  const discountPercent = parseInt(body.discount_percent || '0');
  const maxUses = parseInt(body.max_uses || '100');
  const validUntil = body.valid_until || null;

  if (!code || code.length < 3) {
    return json({ error: 'Code required (min 3 chars)' }, { status: 400 });
  }

  const id = crypto.randomUUID();
  await c.env.DB.prepare(
    `INSERT INTO coupons (id, code, discount_percent, bonus_credits, max_uses, valid_until)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(id, code, discountPercent, bonusCredits, maxUses, validUntil).run();

  return json({ id, code, discountPercent, bonusCredits, maxUses }, { status: 201 });
});

// GET /admin/coupons — list all coupons with usage stats
admin.get('/coupons', async (c) => {
  const coupons = await c.env.DB.prepare(
    'SELECT * FROM coupons ORDER BY created_at DESC'
  ).all();
  return json({ coupons: coupons.results });
});

// DELETE /admin/coupons/:code — deactivate a coupon by code
admin.delete('/coupons/:code', async (c) => {
  const code = c.req.param('code').toUpperCase();
  const result = await c.env.DB.prepare(
    'UPDATE coupons SET active = 0 WHERE code = ?'
  ).bind(code).run();

  if (result.meta.changes === 0) {
    return json({ error: 'Coupon not found' }, { status: 404 });
  }
  return json({ deactivated: true, code });
});

// GET /admin/revenue/ltv — average customer lifetime value across all paying tenants
admin.get('/revenue/ltv', async (c) => {
  const ltv = await c.env.DB.prepare(
    `SELECT AVG(total_spent) as avg_ltv, MAX(total_spent) as max_ltv,
            AVG(julianday('now') - julianday(created_at)) as avg_lifetime_days
     FROM tenants WHERE total_spent > 0`
  ).first();
  return json({
    avgLtv: ltv?.avg_ltv || 0,
    maxLtv: ltv?.max_ltv || 0,
    avgLifetimeDays: Math.round((ltv as any)?.avg_lifetime_days || 0),
  });
});

// GET /admin/revenue/forecast — simple linear ARR projection based on last 6 months
admin.get('/revenue/forecast', async (c) => {
  const monthly = await c.env.DB.prepare(
    `SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as total
     FROM credit_transactions WHERE type = 'purchase'
     GROUP BY month ORDER BY month DESC LIMIT 6`
  ).all();

  const months = monthly.results as any[];
  const avgMonthly = months.length > 0
    ? months.reduce((s: number, m: any) => s + (m.total || 0), 0) / months.length
    : 0;

  return json({
    historicalMonths: months,
    avgMonthlyRevenue: Math.round(avgMonthly * 100) / 100,
    projectedArr: Math.round(avgMonthly * 12 * 100) / 100,
    confidence: months.length >= 3 ? 'medium' : 'low',
  });
});
