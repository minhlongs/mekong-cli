/**
 * Tenant Isolation routes — data access control and violation auditing
 * Mount at: /v1/isolation
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createIsolationContext,
  getIsolationScore,
  getTenantDataScope,
  getViolationHistory,
} from '../services/tenant-isolation-service';

export const tenantIsolationV2 = new Hono<{ Bindings: Env }>();

// All routes require authentication
tenantIsolationV2.use('*', auth());

/**
 * GET /v1/isolation/status — isolation context for the current request
 */
tenantIsolationV2.get('/status', async (c) => {
  try {
    const { tenantId, tier, permissions } = getTenant(c);
    const requestId = c.req.header('X-Request-Id') ?? crypto.randomUUID();
    const ctx = createIsolationContext(tenantId, tier, permissions, requestId);
    return json({ success: true, data: ctx });
  } catch (err) {
    return json({ error: 'Failed to get isolation status', code: 'ISOLATION_STATUS_ERROR' }, { status: 500 });
  }
});

/**
 * GET /v1/isolation/scope — data scope (tables + row counts) for this tenant
 */
tenantIsolationV2.get('/scope', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const tables = await getTenantDataScope(c.env.DB, tenantId);
    const total_records = tables.reduce((sum, t) => sum + t.row_count, 0);
    return json({ success: true, data: { tables, total_records } });
  } catch (err) {
    return json({ error: 'Failed to get data scope', code: 'ISOLATION_SCOPE_ERROR' }, { status: 500 });
  }
});

/**
 * GET /v1/isolation/score — isolation health score (100 = clean, -10 per violation)
 */
tenantIsolationV2.get('/score', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const score = await getIsolationScore(c.env.DB, tenantId);
    return json({ success: true, data: { tenant_id: tenantId, score } });
  } catch (err) {
    return json({ error: 'Failed to get isolation score', code: 'ISOLATION_SCORE_ERROR' }, { status: 500 });
  }
});

/**
 * GET /v1/isolation/violations — violation history
 * Admin (X-Admin-Key) sees all; authenticated tenant sees own only
 * Query: ?limit=50
 */
tenantIsolationV2.get('/violations', async (c) => {
  try {
    const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
    const isAdmin = c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;

    if (isAdmin) {
      const violations = await getViolationHistory(c.env.DB, undefined, limit);
      return json({ success: true, data: violations });
    }

    const { tenantId } = getTenant(c);
    const violations = await getViolationHistory(c.env.DB, tenantId, limit);
    return json({ success: true, data: violations });
  } catch (err) {
    return json({ error: 'Failed to get violations', code: 'ISOLATION_VIOLATIONS_ERROR' }, { status: 500 });
  }
});
