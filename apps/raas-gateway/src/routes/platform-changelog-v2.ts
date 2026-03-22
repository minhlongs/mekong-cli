/**
 * Platform Changelog V2 routes — versioned entries, subscriptions, read tracking
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createEntry,
  listEntries,
  getEntry,
  updateEntry,
  publishEntry,
  subscribeToChangelog,
  getSubscription,
  markAsRead,
  getUnreadCount,
  getAdminChangelogStats,
} from '../services/platform-changelog-v2-service';

export const platformChangelogV2 = new Hono<{ Bindings: Env }>();

/** Admin auth helper — returns 401 if key missing or wrong */
function requireAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY && !!c.env.ADMIN_API_KEY;
}

// ── Public endpoints ──────────────────────────────────────────────────────────

/** GET /entries — list published changelog entries */
platformChangelogV2.get('/entries', async (c) => {
  try {
    const { category, severity, limit, offset } = c.req.query() as Record<string, string>;
    const entries = await listEntries(c.env.DB, {
      category,
      severity,
      limit: limit ? parseInt(limit) : undefined,
      offset: offset ? parseInt(offset) : undefined,
    });
    return json({ entries });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /entries/:entryId — get single published entry */
platformChangelogV2.get('/entries/:entryId', async (c) => {
  try {
    const entry = await getEntry(c.env.DB, c.req.param('entryId'));
    if (!entry || !entry.is_published) return json({ error: 'Not found' }, { status: 404 });
    return json({ entry });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// ── Authenticated tenant endpoints ────────────────────────────────────────────

/** GET /unread — count of unread published entries for tenant */
platformChangelogV2.get('/unread', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const count = await getUnreadCount(c.env.DB, tenant.tenantId);
    return json({ unread_count: count });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /read/:entryId — mark entry as read for tenant */
platformChangelogV2.post('/read/:entryId', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const entryId = c.req.param('entryId');
    const entry = await getEntry(c.env.DB, entryId);
    if (!entry || !entry.is_published) return json({ error: 'Not found' }, { status: 404 });
    await markAsRead(c.env.DB, tenant.tenantId, entryId);
    return json({ success: true });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /subscription — get tenant's changelog subscription */
platformChangelogV2.get('/subscription', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const subscription = await getSubscription(c.env.DB, tenant.tenantId);
    return json({ subscription });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /subscription — create or replace tenant's changelog subscription */
platformChangelogV2.post('/subscription', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{ categories?: string[]; notify_via?: string; webhook_url?: string }>();
    const result = await subscribeToChangelog(c.env.DB, tenant.tenantId, body);
    return json({ subscription_id: result.id }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// ── Admin endpoints ───────────────────────────────────────────────────────────

/** POST /admin/entries — create a new changelog entry */
platformChangelogV2.post('/admin/entries', async (c) => {
  if (!requireAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  try {
    const body = await c.req.json();
    const entry = await createEntry(c.env.DB, body);
    return json({ entry }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** PUT /admin/entries/:entryId — update an existing changelog entry */
platformChangelogV2.put('/admin/entries/:entryId', async (c) => {
  if (!requireAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  try {
    const body = await c.req.json();
    const entry = await updateEntry(c.env.DB, c.req.param('entryId'), body);
    return json({ entry });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /admin/entries/:entryId/publish — publish a changelog entry */
platformChangelogV2.post('/admin/entries/:entryId/publish', async (c) => {
  if (!requireAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  try {
    const entry = await publishEntry(c.env.DB, c.req.param('entryId'));
    return json({ entry });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /admin/stats — changelog stats by category and read rates */
platformChangelogV2.get('/admin/stats', async (c) => {
  if (!requireAdmin(c)) return json({ error: 'Unauthorized' }, { status: 401 });
  try {
    const stats = await getAdminChangelogStats(c.env.DB);
    return json({ stats });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});
