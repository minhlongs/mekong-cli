/**
 * Platform Tenant Scoring routes — list scores, trigger calculation, history, dashboard
 * All endpoints require X-Admin-Key header. Mount path: /admin/tenant-scoring
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { platformTenantScoringService } from '../services/platform-tenant-scoring-service';

export const platformTenantScoring = new Hono<{ Bindings: Env }>();

// Admin auth guard
platformTenantScoring.use('*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /scores — list all current tenant scores
platformTenantScoring.get('/scores', async (c) => {
  try {
    const scores = await platformTenantScoringService.listScores(c.env.DB);
    return c.json({ scores, count: (scores as unknown[]).length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /scores — calculate (or recalculate) score for a tenant
platformTenantScoring.post('/scores', async (c) => {
  try {
    const body = await c.req.json() as { tenant_id?: string };
    if (!body.tenant_id) return c.json({ error: 'tenant_id is required' }, 400);
    const result = await platformTenantScoringService.calculateScore(c.env.DB, body.tenant_id);
    return c.json(result, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /history — score history for a tenant (?tenant_id= required, &limit= optional)
platformTenantScoring.get('/history', async (c) => {
  try {
    const tenantId = c.req.query('tenant_id');
    if (!tenantId) return c.json({ error: 'tenant_id is required' }, 400);
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const history = await platformTenantScoringService.getHistory(c.env.DB, tenantId, limit);
    return c.json({ history, count: (history as unknown[]).length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — aggregate scoring stats across all tenants
platformTenantScoring.get('/dashboard', async (c) => {
  try {
    const dashboard = await platformTenantScoringService.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});
