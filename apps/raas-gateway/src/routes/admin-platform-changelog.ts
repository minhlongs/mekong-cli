/**
 * Admin Platform Changelog routes — changelog entry management and subscriber visibility
 * Admin-only: all routes require X-Admin-Key header matching ADMIN_API_KEY env var
 */

import { Hono } from 'hono';
import { adminPlatformChangelogService } from '../services/admin-platform-changelog';

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

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: { ADMIN_API_KEY: string } }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

/** GET /entries — list all changelog entries */
app.get('/entries', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const result = await adminPlatformChangelogService.listEntries(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ entries: result.data });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** POST /entries — create a new changelog entry */
app.post('/entries', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const body = await c.req.json().catch(() => ({}));
    if (!body.version || !body.title) {
      return c.json({ error: 'version and title are required', code: 'INVALID_INPUT' }, 400);
    }
    const result = await adminPlatformChangelogService.createEntry(c.env.DB, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ entry: result.data }, 201);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** GET /subscribers — list all changelog subscribers */
app.get('/subscribers', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const result = await adminPlatformChangelogService.getSubscribers(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ subscribers: result.data });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

/** GET /dashboard — aggregated changelog stats and recent entries */
app.get('/dashboard', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden', code: 'ADMIN_REQUIRED' }, 403);
  try {
    const result = await adminPlatformChangelogService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Failed' }, 500);
  }
});

export { app as adminPlatformChangelog };
