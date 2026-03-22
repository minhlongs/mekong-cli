/**
 * Admin Release Management routes — platform release lifecycle and notes
 * All endpoints: X-Admin-Key required (403 on mismatch)
 * Mount at: /admin/release-management
 */

import { Hono } from 'hono';
import { adminReleaseManagementService } from '../services/admin-release-management';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
  RATE_LIMIT_KV: any;
  SESSION_KV: any;
  AI: any;
  JWT_SECRET=REDACTED: string;
  POLAR_WEBHOOK_SECRET: string;
  TELEGRAM_BOT_TOKEN: string;
  ENVIRONMENT: string;
  LOG_LEVEL: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin-only guard — 403 on missing or wrong key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

/** GET /admin/release-management/releases — list releases
 *  Query params: status (optional, e.g. draft|published|archived)
 */
app.get('/releases', async (c) => {
  try {
    const status = c.req.query('status');
    const result = await adminReleaseManagementService.listReleases(c.env.DB, status);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** POST /admin/release-management/releases — create a new release
 *  Body: { version, title, description?, release_type?, status?, released_at? }
 */
app.post('/releases', async (c) => {
  try {
    const body = await c.req.json<{
      version: string;
      title: string;
      description?: string;
      release_type?: string;
      status?: string;
      released_at?: string;
    }>();

    if (!body.version || !body.title) {
      return c.json({ error: 'version and title are required' }, 400);
    }

    const id = crypto.randomUUID();
    const result = await adminReleaseManagementService.createRelease(c.env.DB, {
      id,
      version: body.version,
      title: body.title,
      description: body.description,
      release_type: body.release_type,
      status: body.status,
      released_at: body.released_at,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** GET /admin/release-management/notes — list release notes
 *  Query params: release_id (optional), category (optional)
 */
app.get('/notes', async (c) => {
  try {
    const releaseId = c.req.query('release_id');
    const category = c.req.query('category');
    const result = await adminReleaseManagementService.getNotes(
      c.env.DB,
      releaseId,
      category
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** GET /admin/release-management/dashboard — release summary stats */
app.get('/dashboard', async (c) => {
  try {
    const result = await adminReleaseManagementService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as adminReleaseManagement };
