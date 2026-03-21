/**
 * Tenant Health routes — current score, history, and factor breakdown
 * Mount at: /v1/health
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { TenantHealthService } from '../services/tenant-health-service';

export const tenantHealth = new Hono<{ Bindings: Env }>();

// All routes require authentication
tenantHealth.use('*', auth());

const svc = new TenantHealthService();

/**
 * GET /v1/health — Calculate fresh health score and persist it
 */
tenantHealth.get('/', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.calculateScore(c.env.DB, tenantId);
    return c.json({ success: true, data: result });
  } catch (err) {
    console.error('[tenantHealth GET /] error:', err);
    return c.json({ success: false, error: 'Failed to calculate health score' }, 500);
  }
});

/**
 * GET /v1/health/history — Historical health scores
 * Query param: limit (default 10, max 100)
 */
tenantHealth.get('/history', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = Math.min(parseInt(c.req.query('limit') ?? '10', 10) || 10, 100);
    const history = await svc.getHistory(c.env.DB, tenantId, limit);
    return c.json({ success: true, data: history });
  } catch (err) {
    console.error('[tenantHealth GET /history] error:', err);
    return c.json({ success: false, error: 'Failed to fetch health history' }, 500);
  }
});

/**
 * GET /v1/health/factors — Detailed scoring factor breakdown with labels
 */
tenantHealth.get('/factors', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.calculateScore(c.env.DB, tenantId);

    const breakdown = {
      overall: { score: result.score, riskLevel: result.riskLevel, calculatedAt: result.calculatedAt },
      factors: [
        {
          key: 'missionSuccess',
          label: 'Mission Success Rate',
          score: result.factors.missionSuccess,
          weight: 30,
          weighted: Math.round(result.factors.missionSuccess * 0.30),
          description: 'Ratio of completed missions vs failed missions',
        },
        {
          key: 'usageTrend',
          label: 'Usage Trend',
          score: result.factors.usageTrend,
          weight: 25,
          weighted: Math.round(result.factors.usageTrend * 0.25),
          description: 'Current month usage compared to previous month',
        },
        {
          key: 'paymentHistory',
          label: 'Payment History',
          score: result.factors.paymentHistory,
          weight: 25,
          weighted: Math.round(result.factors.paymentHistory * 0.25),
          description: 'Payment retries and account suspensions in last 90 days',
        },
        {
          key: 'apiActivity',
          label: 'API Activity',
          score: result.factors.apiActivity,
          weight: 20,
          weighted: Math.round(result.factors.apiActivity * 0.20),
          description: 'API calls in the last 7 days',
        },
      ],
    };

    return c.json({ success: true, data: breakdown });
  } catch (err) {
    console.error('[tenantHealth GET /factors] error:', err);
    return c.json({ success: false, error: 'Failed to fetch factor breakdown' }, 500);
  }
});
