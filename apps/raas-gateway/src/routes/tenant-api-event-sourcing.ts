/**
 * Tenant API Event Sourcing Routes — event store + snapshot access
 *
 * Tenant (auth required):
 *   GET  /events     — list events for current tenant
 *   POST /events     — append new event for current tenant
 *   GET  /snapshots  — list snapshots for current tenant
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview — platform-wide event + snapshot stats
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiEventSourcingService as svc } from '../services/tenant-api-event-sourcing';

interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
}

const app = new Hono<{ Bindings: Bindings }>();

// ---------------------------------------------------------------------------
// Tenant routes
// ---------------------------------------------------------------------------

/** GET /events — list events for the authenticated tenant */
app.get('/events', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const aggregateId = c.req.query('aggregate_id');
    const aggregateType = c.req.query('aggregate_type');
    const limit = parseInt(c.req.query('limit') ?? '100', 10);
    const result = await svc.listEvents(c.env.DB, tenant.tenantId, { aggregateId, aggregateType, limit });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e) {
    return c.json({ error: String(e) }, 500);
  }
});

/** POST /events — append a new event for the authenticated tenant */
app.post('/events', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{
      aggregate_id?: string;
      aggregate_type?: string;
      event_type?: string;
      event_data?: string;
      version?: number;
    }>();
    if (!body.aggregate_id)   return c.json({ error: 'aggregate_id required' }, 400);
    if (!body.aggregate_type) return c.json({ error: 'aggregate_type required' }, 400);
    if (!body.event_type)     return c.json({ error: 'event_type required' }, 400);
    if (!body.event_data)     return c.json({ error: 'event_data required' }, 400);

    const result = await svc.createEvent(c.env.DB, tenant.tenantId, {
      aggregate_id:   body.aggregate_id,
      aggregate_type: body.aggregate_type,
      event_type:     body.event_type,
      event_data:     body.event_data,
      version:        body.version,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (e) {
    return c.json({ error: String(e) }, 500);
  }
});

/** GET /snapshots — list snapshots for the authenticated tenant */
app.get('/snapshots', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const aggregateId = c.req.query('aggregate_id');
    const aggregateType = c.req.query('aggregate_type');
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const result = await svc.getSnapshots(c.env.DB, tenant.tenantId, { aggregateId, aggregateType, limit });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e) {
    return c.json({ error: String(e) }, 500);
  }
});

// ---------------------------------------------------------------------------
// Admin routes
// ---------------------------------------------------------------------------

/** GET /admin/overview — platform-wide event sourcing stats */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e) {
    return c.json({ error: String(e) }, 500);
  }
});

export { app as tenantApiEventSourcing };
