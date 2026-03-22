/**
 * Tenant API Mock Server routes
 * Mount at: /v1/mock
 *
 * GET  /mocks          — list mock endpoints for authenticated tenant
 * POST /mocks          — create a new mock endpoint
 * GET  /requests       — list logged mock requests for authenticated tenant
 * GET  /admin/overview — platform-wide stats (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiMockServerService as svc } from '../services/tenant-api-mock-server';

// Inline Bindings — avoids tight coupling to index.ts Env shape
type Bindings = {
  DB: any;
  ADMIN_API_KEY?: string;
  [key: string]: any;
};

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /mocks — list all mock endpoints for the authenticated tenant
 */
app.get('/mocks', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.listMocks(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[mock GET /mocks] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /mocks — create a new mock endpoint for the authenticated tenant
 * Body: { mock_name, path_pattern, method?, response_status?, response_body?, response_headers?, delay_ms? }
 */
app.post('/mocks', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => null);

    if (!body || typeof body !== 'object') {
      return c.json({ error: 'Invalid JSON body' }, 400);
    }

    const result = await svc.createMock(c.env.DB, tenantId, body);
    if (!result.success) {
      const status = result.error === 'mock_name and path_pattern are required' ? 400 : 500;
      return c.json({ error: result.error }, status);
    }
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    console.error('[mock POST /mocks] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /requests — list recent mock request logs for the authenticated tenant
 * Query param: limit (default 50, max 200)
 */
app.get('/requests', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '50', 10) || 50;
    const result = await svc.getRequests(c.env.DB, tenantId, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[mock GET /requests] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /admin/overview — platform-wide mock stats (admin only)
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    const expected = c.env.ADMIN_API_KEY;

    if (!expected || key !== expected) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    console.error('[mock GET /admin/overview] error:', err);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as tenantApiMockServer };
