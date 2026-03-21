/**
 * Dashboard routes — tenant aggregated stats endpoint
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';

export const dashboard = new Hono<{ Bindings: Env }>();

/**
 * GET /v1/dashboard — Authenticated endpoint returning tenant's aggregated stats
 * Parallel queries: mission counts, credit summary, webhook success rate, recent missions
 */
dashboard.get('/dashboard', auth(), async (c) => {
  const tenant = getTenant(c);
  const db = c.env.DB;

  // Parallel queries for performance
  const [missions, credits, webhooks, recent] = await Promise.all([
    // Mission counts by status
    db.prepare(
      `SELECT status, COUNT(*) as count FROM missions WHERE tenant_id = ? GROUP BY status`
    ).bind(tenant.tenantId).all(),
    // Credit summary
    db.prepare(
      `SELECT
        SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as earned,
        SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as spent
       FROM credit_transactions WHERE tenant_id = ?`
    ).bind(tenant.tenantId).first<{ earned: number | null; spent: number | null }>(),
    // Webhook success rate (last 30 days)
    db.prepare(
      `SELECT
        COUNT(*) as total,
        SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered
       FROM webhook_delivery_logs
       WHERE tenant_id = ? AND created_at > datetime('now', '-30 days')`
    ).bind(tenant.tenantId).first<{ total: number; delivered: number | null }>(),
    // Recent 5 missions
    db.prepare(
      `SELECT id, goal, status, created_at FROM missions
       WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 5`
    ).bind(tenant.tenantId).all(),
  ]);

  const missionResults = missions.results || [];
  const totalMissions = missionResults.reduce(
    (sum, r) => sum + (r.count as number), 0
  );

  const webhookTotal = webhooks?.total ?? 0;
  const webhookDelivered = (webhooks?.delivered as number) ?? 0;
  const successRate = webhookTotal > 0
    ? Math.round((webhookDelivered / webhookTotal) * 100)
    : 100;

  return c.json({
    missions: {
      byStatus: missionResults,
      total: totalMissions,
    },
    credits: {
      earned: credits?.earned ?? 0,
      spent: credits?.spent ?? 0,
    },
    webhooks: {
      total: webhookTotal,
      delivered: webhookDelivered,
      successRate,
    },
    recentMissions: recent.results || [],
  });
});
