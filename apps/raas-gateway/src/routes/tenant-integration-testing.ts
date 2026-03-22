/**
 * Tenant Integration Testing routes — configs, results, admin overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantIntegrationTestingService } from '../services/tenant-integration-testing-service';

const app = new Hono<{ Bindings: Env }>();

// ── Admin auth helper ──────────────────────────────────────────────────────────

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Tenant routes ──────────────────────────────────────────────────────────────

/**
 * GET /v1/tenant-integration-testing/configs — List test configs for tenant
 */
app.get('/configs', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const configs = await tenantIntegrationTestingService.listConfigs(c.env.DB, tenant.tenantId);
    return json({ configs, total: configs.length });
  } catch (err) {
    return json({ error: 'Failed to list configs', details: String(err) }, { status: 500 });
  }
});

/**
 * POST /v1/tenant-integration-testing/configs — Create test config for tenant
 */
app.post('/configs', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    test_name?: string;
    target_endpoint?: string;
    method?: string;
    expected_status?: number;
    headers_json?: string;
    body_json?: string;
    schedule_cron?: string;
  };

  if (!body.test_name || !body.target_endpoint) {
    return json({ error: 'test_name and target_endpoint are required' }, { status: 400 });
  }

  try {
    const config = await tenantIntegrationTestingService.createConfig(c.env.DB, tenant.tenantId, {
      test_name: body.test_name,
      target_endpoint: body.target_endpoint,
      method: body.method,
      expected_status: body.expected_status,
      headers_json: body.headers_json,
      body_json: body.body_json,
      schedule_cron: body.schedule_cron,
    });
    return json(config, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to create config', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /v1/tenant-integration-testing/results — Get test results for tenant
 * Query: ?config_id=<id> (optional filter)
 */
app.get('/results', auth(), async (c) => {
  const tenant = getTenant(c);
  const configId = c.req.query('config_id');
  try {
    const results = await tenantIntegrationTestingService.getResults(c.env.DB, tenant.tenantId, configId);
    return json({ results, total: results.length });
  } catch (err) {
    return json({ error: 'Failed to get results', details: String(err) }, { status: 500 });
  }
});

// ── Admin routes ───────────────────────────────────────────────────────────────

/**
 * GET /v1/tenant-integration-testing/admin/overview — Cross-tenant overview (X-Admin-Key)
 */
app.get('/admin/overview', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Unauthorized' }, { status: 403 });
  try {
    const overview = await tenantIntegrationTestingService.getAdminOverview(c.env.DB);
    return json(overview);
  } catch (err) {
    return json({ error: 'Failed to get admin overview', details: String(err) }, { status: 500 });
  }
});

export { app as tenantIntegrationTesting };
