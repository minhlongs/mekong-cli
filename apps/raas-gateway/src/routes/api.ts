/**
 * API v1 routes with authentication
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { rateLimit } from '../middleware/rate-limiter';
import { json, notFound } from '../utils/response';
import { missions } from './missions';
import { analytics } from './analytics';

export const api = new Hono<{ Bindings: Env }>();

// API root - no auth required to see available endpoints
api.get('/', (c) => {
  return c.json({
    name: 'RaaS Gateway API',
    version: 'v1',
    endpoints: {
      missions: '/v1/missions',
      credits: '/v1/credits',
      tenants: '/v1/tenants',
      me: '/v1/me',
    },
  });
});

// All other /v1/* routes require authentication
api.use('/*', auth());
// Apply rate limiting after auth (requires tenant context)
api.use('/*', rateLimit());

// Get current tenant info
api.get('/me', (c) => {
  const tenant = getTenant(c);
  return json({
    tenantId: tenant.tenantId,
    tier: tenant.tier,
    permissions: tenant.permissions,
  });
});

// Mission routes
api.route('/missions', missions);

// Analytics
api.route('/analytics', analytics);

// Admin stats (requires admin permission)
api.get('/admin/stats', async (c) => {
  const tenant = getTenant(c);
  if (!tenant.permissions.includes('admin')) {
    return json({ error: 'Admin required', code: 'FORBIDDEN' }, { status: 403 });
  }

  const [tenantCount, missionStats, todayMissions, revenue, errors] = await Promise.all([
    c.env.DB.prepare('SELECT COUNT(*) as c FROM tenants WHERE active=1').first<{c:number}>(),
    c.env.DB.prepare('SELECT COUNT(*) as total, SUM(CASE WHEN status=\'completed\' THEN 1 ELSE 0 END) as completed, SUM(CASE WHEN status=\'failed\' THEN 1 ELSE 0 END) as failed FROM missions').first<{total:number;completed:number;failed:number}>(),
    c.env.DB.prepare("SELECT COUNT(*) as c FROM missions WHERE created_at >= datetime('now','start of day')").first<{c:number}>(),
    c.env.DB.prepare('SELECT COALESCE(SUM(total_spent),0) as spent, COALESCE(SUM(total_earned),0) as earned FROM tenants').first<{spent:number;earned:number}>(),
    c.env.DB.prepare("SELECT COUNT(*) as c FROM missions WHERE status='failed'").first<{c:number}>(),
  ]);

  const total = missionStats?.total ?? 0;
  const errorRate = total > 0 ? ((errors?.c ?? 0) / total * 100).toFixed(1) : '0.0';

  return json({
    tenants: tenantCount?.c ?? 0,
    missions: { total, completed: missionStats?.completed ?? 0, failed: missionStats?.failed ?? 0, today: todayMissions?.c ?? 0 },
    credits: { totalEarned: revenue?.earned ?? 0, totalSpent: revenue?.spent ?? 0 },
    errorRate: `${errorRate}%`,
    timestamp: new Date().toISOString(),
  });
});

// Tenants routes (signup is public, mounted at route-level to bypass auth)
