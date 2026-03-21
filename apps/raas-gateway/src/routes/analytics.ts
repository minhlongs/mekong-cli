/**
 * Analytics routes — tenant usage stats and dashboard data
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const analytics = new Hono<{ Bindings: Env }>();

/**
 * GET /analytics — Tenant usage dashboard
 */
analytics.get('/', async (c) => {
  const tenant = getTenant(c);
  const tid = tenant.tenantId;

  // Run all queries in parallel
  const [
    missionStats,
    complexityStats,
    statusStats,
    creditBalance,
    recentActivity,
  ] = await Promise.all([
    // Total missions + credits spent
    c.env.DB.prepare(
      `SELECT COUNT(*) as total, COALESCE(SUM(credits_cost),0) as totalCost
       FROM missions WHERE tenant_id = ?`
    ).bind(tid).first<{ total: number; totalCost: number }>(),

    // Missions by complexity
    c.env.DB.prepare(
      `SELECT complexity, COUNT(*) as count
       FROM missions WHERE tenant_id = ?
       GROUP BY complexity`
    ).bind(tid).all<{ complexity: string; count: number }>(),

    // Missions by status
    c.env.DB.prepare(
      `SELECT status, COUNT(*) as count
       FROM missions WHERE tenant_id = ?
       GROUP BY status`
    ).bind(tid).all<{ status: string; count: number }>(),

    // Current credit balance
    c.env.DB.prepare(
      'SELECT balance, total_earned, total_spent FROM tenants WHERE id = ?'
    ).bind(tid).first<{ balance: number; total_earned: number; total_spent: number }>(),

    // Last 7 days activity (missions per day)
    c.env.DB.prepare(
      `SELECT DATE(created_at) as day, COUNT(*) as count, SUM(credits_cost) as cost
       FROM missions WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')
       GROUP BY DATE(created_at) ORDER BY day DESC`
    ).bind(tid).all<{ day: string; count: number; cost: number }>(),
  ]);

  return json({
    summary: {
      totalMissions: missionStats?.total ?? 0,
      totalCreditsUsed: missionStats?.totalCost ?? 0,
      balance: creditBalance?.balance ?? 0,
      totalEarned: creditBalance?.total_earned ?? 0,
      totalSpent: creditBalance?.total_spent ?? 0,
    },
    byComplexity: Object.fromEntries(
      (complexityStats.results || []).map(r => [r.complexity, r.count])
    ),
    byStatus: Object.fromEntries(
      (statusStats.results || []).map(r => [r.status, r.count])
    ),
    daily: (recentActivity.results || []).map(r => ({
      date: r.day,
      missions: r.count,
      creditsUsed: r.cost,
    })),
  });
});
