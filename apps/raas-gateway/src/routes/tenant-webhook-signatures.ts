/**
 * Tenant Webhook Signatures routes
 * Mount at: /v1/tenant-webhook-signatures
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  listSignatures,
  createSignature,
  getVerifications,
  getAdminOverview,
} from '../services/tenant-webhook-signatures';

const app = new Hono<{ Bindings: Env }>();

/** GET /signatures — list tenant webhook signatures */
app.get('/signatures', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await listSignatures(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** POST /signatures — create a new webhook signature for the tenant */
app.post('/signatures', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      secret_key: string;
      algorithm?: string;
      is_active?: number;
    }>();

    if (!body.secret_key) {
      return c.json({ success: false, error: 'secret_key is required' }, 400);
    }

    const signature = await createSignature(c.env.DB, tenantId, body);
    return c.json({ success: true, data: signature }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /verifications — list signature verification logs for the tenant */
app.get('/verifications', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await getVerifications(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /admin/overview — admin: platform-wide webhook signatures overview */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  try {
    const data = await getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export { app as tenantWebhookSignatures };
