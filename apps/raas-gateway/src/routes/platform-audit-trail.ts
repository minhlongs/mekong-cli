/**
 * Platform Audit Trail routes — admin-only audit log management
 *
 * All endpoints require X-Admin-Key header.
 *
 * GET  /entries          — list audit entries (with filters)
 * GET  /stats            — aggregate stats
 * GET  /actor/:actorId   — all actions by an actor
 * GET  /resource/:type/:id — all changes to a resource
 * GET  /search           — text search (q param)
 * GET  /export           — export as array
 * GET  /retention        — list retention configs
 * POST /retention        — set retention config
 * POST /cleanup          — delete expired entries
 * POST /log              — manual log entry (testing)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import {
  logAction,
  getAuditLog,
  getActorHistory,
  getResourceHistory,
  searchAuditLog,
  getAuditStats,
  setRetentionConfig,
  getRetentionConfigs,
  cleanExpiredEntries,
  exportAuditLog,
} from '../services/platform-audit-trail-service';

const app = new Hono<{ Bindings: Env }>();

// Admin authentication middleware
const adminAuth = async (c: any, next: any) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
};

app.use('/*', adminAuth);

/** GET /entries — paginated audit log with optional filters */
app.get('/entries', async (c) => {
  try {
    const q = c.req.query();
    const entries = await getAuditLog(c.env.DB, {
      actorId: q.actorId,
      action: q.action,
      resourceType: q.resourceType,
      resourceId: q.resourceId,
      dateFrom: q.dateFrom,
      dateTo: q.dateTo,
      limit: q.limit ? parseInt(q.limit) : undefined,
      offset: q.offset ? parseInt(q.offset) : undefined,
    });
    return c.json({ entries });
  } catch (err) {
    return c.json({ error: 'Failed to fetch audit log' }, 500);
  }
});

/** GET /stats — aggregate stats (default last 30 days) */
app.get('/stats', async (c) => {
  try {
    const days = c.req.query('days') ? parseInt(c.req.query('days')!) : 30;
    const stats = await getAuditStats(c.env.DB, days);
    return c.json(stats);
  } catch (err) {
    return c.json({ error: 'Failed to fetch stats' }, 500);
  }
});

/** GET /actor/:actorId — action history for a specific actor */
app.get('/actor/:actorId', async (c) => {
  try {
    const { actorId } = c.req.param();
    const limit = c.req.query('limit') ? parseInt(c.req.query('limit')!) : 100;
    const entries = await getActorHistory(c.env.DB, actorId, limit);
    return c.json({ actorId, entries });
  } catch (err) {
    return c.json({ error: 'Failed to fetch actor history' }, 500);
  }
});

/** GET /resource/:type/:id — change history for a specific resource */
app.get('/resource/:type/:id', async (c) => {
  try {
    const { type, id } = c.req.param();
    const entries = await getResourceHistory(c.env.DB, type, id);
    return c.json({ resourceType: type, resourceId: id, entries });
  } catch (err) {
    return c.json({ error: 'Failed to fetch resource history' }, 500);
  }
});

/** GET /search — text search across action, resource_type, changes */
app.get('/search', async (c) => {
  try {
    const q = c.req.query('q');
    if (!q) return c.json({ error: 'q param required' }, 400);
    const entries = await searchAuditLog(c.env.DB, q);
    return c.json({ query: q, entries });
  } catch (err) {
    return c.json({ error: 'Search failed' }, 500);
  }
});

/** GET /export — export filtered entries as array */
app.get('/export', async (c) => {
  try {
    const q = c.req.query();
    const entries = await exportAuditLog(c.env.DB, {
      actorId: q.actorId,
      action: q.action,
      resourceType: q.resourceType,
      resourceId: q.resourceId,
      dateFrom: q.dateFrom,
      dateTo: q.dateTo,
      limit: q.limit ? parseInt(q.limit) : undefined,
    });
    return c.json({ exported: entries.length, entries });
  } catch (err) {
    return c.json({ error: 'Export failed' }, 500);
  }
});

/** GET /retention — list all retention configs */
app.get('/retention', async (c) => {
  try {
    const configs = await getRetentionConfigs(c.env.DB);
    return c.json({ configs });
  } catch (err) {
    return c.json({ error: 'Failed to fetch retention configs' }, 500);
  }
});

/** POST /retention — set retention config for a resource type */
app.post('/retention', async (c) => {
  try {
    const body = await c.req.json();
    const { resourceType, retentionDays, immutable } = body;
    if (!resourceType || !retentionDays) {
      return c.json({ error: 'resourceType and retentionDays required' }, 400);
    }
    const result = await setRetentionConfig(c.env.DB, resourceType, retentionDays, immutable ?? false);
    return c.json({ success: true, ...result });
  } catch (err) {
    return c.json({ error: 'Failed to set retention config' }, 500);
  }
});

/** POST /cleanup — delete entries past retention period */
app.post('/cleanup', async (c) => {
  try {
    const result = await cleanExpiredEntries(c.env.DB);
    return c.json({ success: true, ...result });
  } catch (err) {
    return c.json({ error: 'Cleanup failed' }, 500);
  }
});

/** POST /log — manually log an audit entry (for testing / external ingestion) */
app.post('/log', async (c) => {
  try {
    const body = await c.req.json();
    const { actorType, actorId, action, resourceType, resourceId, changes, metadata } = body;
    if (!actorType || !actorId || !action || !resourceType) {
      return c.json({ error: 'actorType, actorId, action, resourceType required' }, 400);
    }
    const ipAddress = c.req.header('CF-Connecting-IP') ?? c.req.header('X-Forwarded-For');
    const userAgent = c.req.header('User-Agent');
    const result = await logAction(c.env.DB, {
      actorType, actorId, action, resourceType, resourceId, changes, metadata, ipAddress, userAgent,
    });
    return c.json({ success: true, ...result }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to log action' }, 500);
  }
});

export { app as platformAuditTrail };
