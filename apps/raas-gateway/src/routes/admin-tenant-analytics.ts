/**
 * Admin Tenant Analytics routes — health scores, usage trends, risk indicators
 * All endpoints require X-Admin-Key header. Mount path: /admin/tenant-analytics
 */

import { Hono } from 'hono';
import { adminTenantAnalyticsService as svc } from '../services/admin-tenant-analytics-service';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// --- Health Scores ---

// GET /health/:tenantId — latest health score for tenant
app.get('/health/:tenantId', async (c) => {
  try {
    const score = await svc.getHealthScore(c.env.DB, c.req.param('tenantId'));
    if (!score) return c.json({ error: 'No health score found' }, 404);
    return c.json(score);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /health/:tenantId/calculate — recalculate health score
app.post('/health/:tenantId/calculate', async (c) => {
  try {
    const score = await svc.calculateHealthScore(c.env.DB, c.req.param('tenantId'));
    return c.json(score, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /health — list health scores with optional filters
app.get('/health', async (c) => {
  try {
    const filters = {
      risk_level: c.req.query('risk_level'),
      tenant_id: c.req.query('tenant_id'),
    };
    const scores = await svc.listHealthScores(c.env.DB, filters);
    return c.json({ scores, count: scores.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// --- Usage Trends ---

// GET /trends/:tenantId — usage trends for tenant
app.get('/trends/:tenantId', async (c) => {
  try {
    const periodsParam = c.req.query('periods');
    const periods = periodsParam ? periodsParam.split(',') : undefined;
    const trends = await svc.getUsageTrends(c.env.DB, c.req.param('tenantId'), periods);
    return c.json({ trends, count: trends.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /trends/:tenantId — record a usage trend entry
app.post('/trends/:tenantId', async (c) => {
  try {
    const body = await c.req.json<{
      period: string; missions_count?: number; api_calls?: number; credits_used?: number; revenue_cents?: number;
    }>();
    if (!body.period) return c.json({ error: 'period is required' }, 400);
    const trend = await svc.recordUsageTrend(c.env.DB, c.req.param('tenantId'), body);
    return c.json(trend, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// --- Risk Indicators ---

// GET /risks — list risk indicators with optional filters
app.get('/risks', async (c) => {
  try {
    const resolvedParam = c.req.query('resolved');
    const filters = {
      tenant_id: c.req.query('tenant_id'),
      severity: c.req.query('severity'),
      indicator_type: c.req.query('indicator_type'),
      resolved: resolvedParam !== undefined ? resolvedParam === 'true' : undefined,
    };
    const risks = await svc.listRiskIndicators(c.env.DB, filters);
    return c.json({ risks, count: risks.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /risks/:tenantId — create a risk indicator
app.post('/risks/:tenantId', async (c) => {
  try {
    const body = await c.req.json<{ indicator_type: string; severity?: string; description?: string }>();
    if (!body.indicator_type) return c.json({ error: 'indicator_type is required' }, 400);
    const risk = await svc.createRiskIndicator(c.env.DB, c.req.param('tenantId'), body);
    return c.json(risk, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /risks/:id/resolve — mark risk indicator as resolved
app.post('/risks/:id/resolve', async (c) => {
  try {
    const risk = await svc.resolveRiskIndicator(c.env.DB, c.req.param('id'));
    if (!risk) return c.json({ error: 'Risk indicator not found' }, 404);
    return c.json(risk);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// --- Reports & Dashboard ---

// GET /report/:tenantId — full tenant analytics report
app.get('/report/:tenantId', async (c) => {
  try {
    const report = await svc.getTenantReport(c.env.DB, c.req.param('tenantId'));
    return c.json(report);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — aggregated admin overview across all tenants
app.get('/dashboard', async (c) => {
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminTenantAnalytics };
