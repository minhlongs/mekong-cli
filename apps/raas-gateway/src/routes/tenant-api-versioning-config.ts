/**
 * Tenant API Versioning Config routes
 * Mount at: /v1/api-versioning
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiVersioningConfigService as svc } from '../services/tenant-api-versioning-config';

type Bindings = {
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

const app = new Hono<{ Bindings: Bindings }>();

// ── Configs (tenant-scoped, auth required) ────────────────────────────────────

app.use('/configs', auth());

app.get('/configs', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.listConfigs(c.env.DB, tenantId);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

app.post('/configs', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    const result = await svc.createConfig(c.env.DB, tenantId, body);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// ── Mappings (tenant-scoped, auth required) ───────────────────────────────────

app.use('/mappings', auth());

app.get('/mappings', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.getMappings(c.env.DB, tenantId);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// ── Admin overview (admin key required) ──────────────────────────────────────

app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  try {
    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export { app as tenantApiVersioningConfig };
