/**
 * Analytics API Routes
 */

import { Hono } from 'hono';
import { getTenantMetrics, getAnalyticsSummary, getRateLimitAnalytics, recordUsage } from '../lib/analytics';
import { requireLicenseMiddleware, LicenseTier } from '../lib/raas-gate';

const analytics = new Hono();

// Middleware: Require PRO license
analytics.use('/*', requireLicenseMiddleware(LicenseTier.PRO));

/**
 * GET /api/analytics/usage
 * Get usage metrics for current tenant
 */
analytics.get('/usage', async (c) => {
  const tenantId = c.req.header('x-tenant-id') || 'default';

  try {
    recordUsage(tenantId, '/api/analytics/usage');
    const metrics = await getTenantMetrics(tenantId);
    return c.json(metrics);
  } catch (error) {
    return c.json({ error: 'Failed to get usage metrics' }, 500);
  }
});

/**
 * GET /api/analytics/summary
 * Get aggregated analytics across all tenants
 */
analytics.get('/summary', async (c) => {
  try {
    recordUsage('system', '/api/analytics/summary');
    const summary = await getAnalyticsSummary();
    return c.json(summary);
  } catch (error) {
    return c.json({ error: 'Failed to get analytics summary' }, 500);
  }
});

/**
 * GET /api/analytics/limits
 * Get rate limit analytics
 */
analytics.get('/limits', async (c) => {
  try {
    recordUsage('system', '/api/analytics/limits');
    const limits = await getRateLimitAnalytics();
    return c.json(limits);
  } catch (error) {
    return c.json({ error: 'Failed to get rate limit analytics' }, 500);
  }
});

export { analytics };
