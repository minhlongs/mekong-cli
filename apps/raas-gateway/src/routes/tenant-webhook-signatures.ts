/**
 * Tenant Webhook Signatures routes
 * Manage webhook signing keys and verification logs
 * Mount at: /v1/webhook-signatures
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantWebhookSignaturesService } from '../services/tenant-webhook-signatures';

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

/** GET /keys — list signing keys for authenticated tenant */
app.get('/keys', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantWebhookSignaturesService.listKeys(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
});

/** POST /keys — create a new signing key for authenticated tenant */
app.post('/keys', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ keyName: string; secret: string; algorithm?: string }>();

    if (!body.keyName || !body.secret) {
      return c.json({ error: 'keyName and secret are required' }, 400);
    }

    const result = await tenantWebhookSignaturesService.createKey(c.env.DB, tenantId, {
      keyName: body.keyName,
      secret: body.secret,
      algorithm: body.algorithm,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
});

/** GET /logs — list signature verification logs for authenticated tenant */
app.get('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
    const result = await tenantWebhookSignaturesService.getLogs(c.env.DB, tenantId, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
});

/** GET /admin/overview — platform-wide overview; requires X-Admin-Key header */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await tenantWebhookSignaturesService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
});

export { app as tenantWebhookSignatures };
