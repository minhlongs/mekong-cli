/**
 * Platform Announcements routes — system-wide banners and maintenance windows
 * Public: GET /maintenance
 * Auth (tenant): GET /active, POST /dismiss/:announcementId
 * Admin (X-Admin-Key): POST /admin/create, GET /admin/list, PUT /admin/:id,
 *                      DELETE /admin/:id, GET /admin/stats, POST /admin/cleanup
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createAnnouncement,
  listActiveAnnouncements,
  getAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  dismissAnnouncement,
  getUndismissedAnnouncements,
  getAnnouncementStats,
  getMaintenanceWindows,
  cleanExpiredAnnouncements,
} from '../services/platform-announcements-service';
import type { AnnouncementType, AudienceTier } from '../services/platform-announcements-service';

const app = new Hono<{ Bindings: Env }>();

// ── Admin auth middleware ───────────────────────────────────────────────────────

const requireAdminKey = async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401);
  }
  await next();
};

// ── Public routes ──────────────────────────────────────────────────────────────

/** GET /maintenance — upcoming + ongoing maintenance windows (no auth required) */
app.get('/maintenance', async (c) => {
  try {
    const windows = await getMaintenanceWindows(c.env.DB);
    return c.json({ ok: true, count: windows.length, data: windows });
  } catch (err) {
    return c.json({ error: 'Failed to fetch maintenance windows', details: String(err) }, 500);
  }
});

// ── Tenant auth routes ─────────────────────────────────────────────────────────

/** GET /active — active undismissed announcements for authenticated tenant */
app.get('/active', auth(), async (c) => {
  try {
    const { tenantId, tier } = getTenant(c);
    const announcements = await getUndismissedAnnouncements(c.env.DB, tenantId, tier);
    return c.json({ ok: true, count: announcements.length, data: announcements });
  } catch (err) {
    return c.json({ error: 'Failed to fetch announcements', details: String(err) }, 500);
  }
});

/** POST /dismiss/:announcementId — dismiss an announcement for the authenticated tenant */
app.post('/dismiss/:announcementId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const announcementId = c.req.param('announcementId');

    const announcement = await getAnnouncement(c.env.DB, announcementId);
    if (!announcement) {
      return c.json({ error: 'Announcement not found' }, 404);
    }

    await dismissAnnouncement(c.env.DB, tenantId, announcementId);
    return c.json({ ok: true, dismissed: announcementId });
  } catch (err) {
    return c.json({ error: 'Failed to dismiss announcement', details: String(err) }, 500);
  }
});

// ── Admin routes ───────────────────────────────────────────────────────────────

const VALID_TYPES: AnnouncementType[] = ['info', 'warning', 'maintenance', 'feature', 'critical'];
const VALID_AUDIENCES: AudienceTier[] = ['all', 'free', 'pro', 'enterprise'];

/** POST /admin/create — create a new announcement */
app.post('/admin/create', requireAdminKey, async (c) => {
  try {
    const body = await c.req.json<{
      title?: string;
      content?: string;
      type?: string;
      priority?: number;
      target_audience?: string;
      starts_at?: string;
      ends_at?: string;
      created_by?: string;
    }>();

    if (!body.title || !body.content) {
      return c.json({ error: 'title and content are required' }, 400);
    }
    if (body.type && !VALID_TYPES.includes(body.type as AnnouncementType)) {
      return c.json({ error: `type must be one of: ${VALID_TYPES.join(', ')}` }, 400);
    }
    if (body.target_audience && !VALID_AUDIENCES.includes(body.target_audience as AudienceTier)) {
      return c.json({ error: `target_audience must be one of: ${VALID_AUDIENCES.join(', ')}` }, 400);
    }

    const announcement = await createAnnouncement(
      c.env.DB,
      body.title,
      body.content,
      (body.type as AnnouncementType) ?? 'info',
      body.priority ?? 0,
      (body.target_audience as AudienceTier) ?? 'all',
      body.starts_at,
      body.ends_at,
      body.created_by,
    );
    return c.json({ ok: true, data: announcement }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create announcement', details: String(err) }, 500);
  }
});

/** GET /admin/list — list all announcements (active and inactive) */
app.get('/admin/list', requireAdminKey, async (c) => {
  try {
    // No tier filter — admins see all
    const announcements = await listActiveAnnouncements(c.env.DB);
    return c.json({ ok: true, count: announcements.length, data: announcements });
  } catch (err) {
    return c.json({ error: 'Failed to list announcements', details: String(err) }, 500);
  }
});

/** PUT /admin/:announcementId — update an existing announcement */
app.put('/admin/:announcementId', requireAdminKey, async (c) => {
  try {
    const announcementId = c.req.param('announcementId');
    const body: Record<string, unknown> = await c.req.json<Record<string, unknown>>().catch(() => ({}));

    const existing = await getAnnouncement(c.env.DB, announcementId);
    if (!existing) {
      return c.json({ error: 'Announcement not found' }, 404);
    }

    const allowedFields = ['title', 'content', 'type', 'priority', 'target_audience', 'starts_at', 'ends_at', 'is_active'];
    const updates: Record<string, unknown> = {};
    for (const field of allowedFields) {
      if (field in body) updates[field] = body[field];
    }

    if (updates.type && !VALID_TYPES.includes(updates.type as AnnouncementType)) {
      return c.json({ error: `type must be one of: ${VALID_TYPES.join(', ')}` }, 400);
    }

    const updated = await updateAnnouncement(c.env.DB, announcementId, updates as any);
    return c.json({ ok: true, data: updated });
  } catch (err) {
    return c.json({ error: 'Failed to update announcement', details: String(err) }, 500);
  }
});

/** DELETE /admin/:announcementId — hard delete an announcement */
app.delete('/admin/:announcementId', requireAdminKey, async (c) => {
  try {
    const announcementId = c.req.param('announcementId');

    const existing = await getAnnouncement(c.env.DB, announcementId);
    if (!existing) {
      return c.json({ error: 'Announcement not found' }, 404);
    }

    await deleteAnnouncement(c.env.DB, announcementId);
    return c.json({ ok: true, deleted: announcementId });
  } catch (err) {
    return c.json({ error: 'Failed to delete announcement', details: String(err) }, 500);
  }
});

/** GET /admin/stats — announcement stats by type, active count, dismissal rate */
app.get('/admin/stats', requireAdminKey, async (c) => {
  try {
    const stats = await getAnnouncementStats(c.env.DB);
    return c.json({ ok: true, data: stats });
  } catch (err) {
    return c.json({ error: 'Failed to fetch stats', details: String(err) }, 500);
  }
});

/** POST /admin/cleanup — deactivate expired announcements */
app.post('/admin/cleanup', requireAdminKey, async (c) => {
  try {
    const deactivated = await cleanExpiredAnnouncements(c.env.DB);
    return c.json({ ok: true, deactivated });
  } catch (err) {
    return c.json({ error: 'Failed to clean expired announcements', details: String(err) }, 500);
  }
});

export { app as platformAnnouncements };
