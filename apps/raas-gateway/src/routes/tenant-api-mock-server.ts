/**
 * Tenant API Mock Server routes
 * Mount at: /v1/mock
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiMockServerService as svc } from '../services/tenant-api-mock-server-service';

const app = new Hono<{ Bindings: Env }>();

// All tenant routes require authentication
app.use('*', auth());

/**
 * GET /v1/mock/mocks — List all active mocks for the authenticated tenant
 */
app.get('/mocks', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const mocks = await svc.listMocks(c.env.DB, tenantId);
    return c.json({ success: true, data: mocks });
  } catch (err) {
    console.error('[mock GET /mocks] error:', err);
    return c.json({ success: false, error: 'Failed to list mocks' }, 500);
  }
});

/**
 * POST /v1/mock/mocks — Create a new mock endpoint
 * Body: { mock_path, method?, response_status?, response_body_json?, response_headers_json?, delay_ms? }
 */
app.post('/mocks', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body?.mock_path) {
      return c.json({ success: false, error: 'mock_path is required' }, 400);
    }
    const created = await svc.createMock(c.env.DB, tenantId, body);
    return c.json({ success: true, data: created }, 201);
  } catch (err) {
    console.error('[mock POST /mocks] error:', err);
    return c.json({ success: false, error: 'Failed to create mock' }, 500);
  }
});

/**
 * GET /v1/mock/requests?mock_id=&limit= — Request log for a mock endpoint
 */
app.get('/requests', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const mockId = c.req.query('mock_id');
    if (!mockId) {
      return c.json({ success: false, error: 'mock_id query param is required' }, 400);
    }
    const limit = parseInt(c.req.query('limit') ?? '50', 10) || 50;
    const requests = await svc.getRequests(c.env.DB, tenantId, mockId, limit);
    return c.json({ success: true, data: requests });
  } catch (err) {
    console.error('[mock GET /requests] error:', err);
    return c.json({ success: false, error: 'Failed to fetch requests' }, 500);
  }
});

/**
 * GET /v1/mock/admin/overview — Platform-wide stats (admin only)
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ success: false, error: 'Forbidden' }, 403);
    }
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    console.error('[mock GET /admin/overview] error:', err);
    return c.json({ success: false, error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as tenantApiMockServer };
