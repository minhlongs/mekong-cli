/**
 * Platform Audit Trail routes — Wave 50
 *
 * Auth routes (X-Tenant-Id header required):
 *   GET  /logs                  — search logs (paginated)
 *   GET  /logs/:id              — get log detail
 *   GET  /retention             — list retention policies
 *   PUT  /retention/:resourceType — upsert retention policy
 *   POST /exports               — request export
 *   GET  /exports               — list exports
 *   GET  /stats                 — per-tenant stats
 *
 * Admin routes (X-Admin-Key header required):
 *   GET  /admin/overview        — global stats + storage usage
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { platformAuditTrailService } from '../services/platform-audit-trail-service';

const app = new Hono<{ Bindings: Env }>();

// Admin middleware: requires ADMIN_API_KEY via X-Admin-Key header
const requireAdmin = async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
};

/** GET /logs — search audit logs for tenant */
app.get('/logs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const q = c.req.query();
    const result = await platformAuditTrailService.searchLogs(c.env.DB, tenantId, {
      action: q.action,
      resourceType: q.resourceType,
      severity: q.severity,
      dateFrom: q.dateFrom,
      dateTo: q.dateTo,
      limit: q.limit ? parseInt(q.limit) : undefined,
      offset: q.offset ? parseInt(q.offset) : undefined,
    });
    return c.json({ ok: true, data: result });
  } catch (err) {
    return c.json({ error: 'Failed to search logs' }, 500);
  }
});

/** GET /logs/:id — get single log entry */
app.get('/logs/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const { id } = c.req.param();
    const log = await platformAuditTrailService.getLogDetail(c.env.DB, tenantId, id);
    if (!log) return c.json({ error: 'Not found' }, 404);
    return c.json({ ok: true, data: log });
  } catch (err) {
    return c.json({ error: 'Failed to fetch log' }, 500);
  }
});

/** GET /retention — list all retention policies */
app.get('/retention', auth(), async (c) => {
  try {
    const policies = await platformAuditTrailService.listRetentionPolicies(c.env.DB);
    return c.json({ ok: true, data: policies });
  } catch (err) {
    return c.json({ error: 'Failed to list retention policies' }, 500);
  }
});

/** PUT /retention/:resourceType — upsert retention policy */
app.put('/retention/:resourceType', auth(), async (c) => {
  try {
    const { resourceType } = c.req.param();
    const body = await c.req.json().catch(() => ({}));
    const result = await platformAuditTrailService.updateRetentionPolicy(c.env.DB, resourceType, {
      retentionDays: body.retentionDays,
      autoArchive: body.autoArchive,
    });
    return c.json({ ok: true, data: result });
  } catch (err) {
    return c.json({ error: 'Failed to update retention policy' }, 500);
  }
});

/** POST /exports — request a new export */
app.post('/exports', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const filters = await c.req.json().catch(() => ({}));
    const result = await platformAuditTrailService.requestExport(c.env.DB, tenantId, filters);
    return c.json({ ok: true, data: result }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to request export' }, 500);
  }
});

/** GET /exports — list exports for tenant */
app.get('/exports', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const exports = await platformAuditTrailService.listExports(c.env.DB, tenantId);
    return c.json({ ok: true, data: exports });
  } catch (err) {
    return c.json({ error: 'Failed to list exports' }, 500);
  }
});

/** GET /stats — per-tenant action + severity stats */
app.get('/stats', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const stats = await platformAuditTrailService.getStats(c.env.DB, tenantId);
    return c.json({ ok: true, data: stats });
  } catch (err) {
    return c.json({ error: 'Failed to fetch stats' }, 500);
  }
});

/** GET /admin/overview — global stats for platform admins */
app.get('/admin/overview', requireAdmin, async (c) => {
  try {
    const overview = await platformAuditTrailService.getAdminOverview(c.env.DB);
    return c.json({ ok: true, data: overview });
  } catch (err) {
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as platformAuditTrail };
