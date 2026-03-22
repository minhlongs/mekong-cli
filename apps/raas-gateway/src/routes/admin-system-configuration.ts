/**
 * Admin System Configuration routes
 * All endpoints protected by X-Admin-Key header
 * GET /configs, POST /configs, GET /history, GET /dashboard
 */

import { Hono } from 'hono';
import { adminSystemConfigurationService as svc } from '../services/admin-system-configuration';

const app = new Hono<{
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
}>();

// Admin auth middleware — all routes require X-Admin-Key
app.use('*', async (c, next) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /configs — list all system configurations
app.get('/configs', async (c) => {
  try {
    const result = await svc.listConfigs(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// POST /configs — create a new system configuration
app.post('/configs', async (c) => {
  try {
    const body = await c.req.json();
    if (!body.config_key || body.config_value === undefined) {
      return c.json({ error: 'config_key and config_value are required' }, 400);
    }
    const result = await svc.createConfig(c.env.DB, {
      config_key: body.config_key,
      config_value: String(body.config_value),
      config_type: body.config_type,
      description: body.description,
      updated_by: body.updated_by,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// GET /history — change history, optional ?config_id and ?limit filters
app.get('/history', async (c) => {
  try {
    const configId = c.req.query('config_id');
    const limit = Number(c.req.query('limit') ?? 50);
    const result = await svc.getHistory(c.env.DB, configId, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// GET /dashboard — aggregate stats and recent changes
app.get('/dashboard', async (c) => {
  try {
    const result = await svc.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as adminSystemConfiguration };
