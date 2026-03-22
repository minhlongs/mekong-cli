/**
 * Tenant API Changelog routes
 *
 * Tenant (auth required):
 *   GET  /entries        — list published changelog entries for tenant
 *   POST /entries        — create a new changelog entry
 *   GET  /subscriptions  — list subscriptions for tenant
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview — platform-wide entry + subscription counts
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { listEntries, createEntry, getSubscriptions, getAdminOverview } from '../services/tenant-api-changelog';

interface Bindings {
  DB: D1Database;
  ADMIN_API_KEY?: string;
  [key: string]: unknown;
}

const app = new Hono<{ Bindings: Bindings }>();

// ---------------------------------------------------------------------------
// Tenant routes (auth required)
// ---------------------------------------------------------------------------

/** GET /entries — list published changelog entries for the authenticated tenant */
app.get('/entries', auth(), async (c) => {
  const tenant = getTenant(c);
  const limit = parseInt(c.req.query('limit') ?? '20', 10);
  const offset = parseInt(c.req.query('offset') ?? '0', 10);

  try {
    const result = await listEntries(c.env.DB, tenant.tenantId, { limit, offset });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list changelog entries' }, 500);
  }
});

/** POST /entries — create a changelog entry for the authenticated tenant */
app.post('/entries', auth(), async (c) => {
  const tenant = getTenant(c);

  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400);
  }

  const version = body.version as string | undefined;
  const title = body.title as string | undefined;
  if (!version || !title) {
    return c.json({ error: 'version and title are required' }, 400);
  }

  try {
    const result = await createEntry(c.env.DB, tenant.tenantId, {
      version,
      title,
      description: body.description as string | undefined,
      change_type: body.change_type as string | undefined,
      published: Boolean(body.published),
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Failed to create changelog entry' }, 500);
  }
});

/** GET /subscriptions — list changelog subscriptions for the authenticated tenant */
app.get('/subscriptions', auth(), async (c) => {
  const tenant = getTenant(c);

  try {
    const result = await getSubscriptions(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list subscriptions' }, 500);
  }
});

// ---------------------------------------------------------------------------
// Admin route (X-Admin-Key)
// ---------------------------------------------------------------------------

/** GET /admin/overview — platform-wide changelog stats */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as tenantApiChangelog };
