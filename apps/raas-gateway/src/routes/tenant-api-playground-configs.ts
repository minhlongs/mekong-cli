/**
 * Tenant API Playground Configs routes
 * Mount at: /v1/playground-configs
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { playgroundConfigsService as svc } from '../services/tenant-api-playground-configs-service';

export const tenantApiPlaygroundConfigs = new Hono<{ Bindings: Env }>();

// All tenant routes require authentication
tenantApiPlaygroundConfigs.use('/configs', auth());
tenantApiPlaygroundConfigs.use('/configs/*', auth());
tenantApiPlaygroundConfigs.use('/executions', auth());

/**
 * GET /configs — List saved playground configs for the authenticated tenant
 */
tenantApiPlaygroundConfigs.get('/configs', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configs = await svc.listConfigs(c.env.DB, tenantId);
    return c.json({ success: true, data: configs });
  } catch (err) {
    console.error('[playgroundConfigs GET /configs]', err);
    return c.json({ success: false, error: 'Failed to list configs' }, 500);
  }
});

/**
 * POST /configs — Save a new playground config
 * Body: { config_name, endpoint, method?, headers_json?, body_json?, is_shared? }
 */
tenantApiPlaygroundConfigs.post('/configs', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.config_name || !body.endpoint) {
      return c.json({ success: false, error: 'config_name and endpoint are required' }, 400);
    }
    const config = await svc.createConfig(c.env.DB, tenantId, body);
    return c.json({ success: true, data: config }, 201);
  } catch (err) {
    console.error('[playgroundConfigs POST /configs]', err);
    return c.json({ success: false, error: 'Failed to create config' }, 500);
  }
});

/**
 * GET /executions — Execution history for the authenticated tenant
 * Query: config_id? (optional filter)
 */
tenantApiPlaygroundConfigs.get('/executions', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configId = c.req.query('config_id');
    const executions = await svc.getExecutions(c.env.DB, tenantId, configId);
    return c.json({ success: true, data: executions });
  } catch (err) {
    console.error('[playgroundConfigs GET /executions]', err);
    return c.json({ success: false, error: 'Failed to fetch executions' }, 500);
  }
});

/**
 * GET /admin/overview — Platform-wide stats (requires X-Admin-Key header)
 */
tenantApiPlaygroundConfigs.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    console.error('[playgroundConfigs GET /admin/overview]', err);
    return c.json({ success: false, error: 'Failed to fetch admin overview' }, 500);
  }
});
