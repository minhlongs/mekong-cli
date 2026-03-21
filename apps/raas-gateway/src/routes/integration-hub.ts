/**
 * Integration Hub routes — connector catalog and tenant integrations
 * Mount at: /v1/integrations
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  getCatalog, getCatalogItem, installIntegration,
  getInstalledIntegrations, getIntegration, updateIntegration,
  uninstallIntegration, logEvent, getEventLog, seedCatalog,
} from '../services/integration-hub-service';

const app = new Hono<{ Bindings: Env }>();

// ── Public: catalog ──────────────────────────────────────────────────────────

/** GET /v1/integrations/catalog — list available integrations */
app.get('/catalog', async (c) => {
  try {
    const { category } = c.req.query();
    const items = await getCatalog(c.env.DB, { category });
    return c.json({ success: true, data: items });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /v1/integrations/catalog/:slug — get catalog item details */
app.get('/catalog/:slug', async (c) => {
  try {
    const item = await getCatalogItem(c.env.DB, c.req.param('slug'));
    if (!item) return c.json({ success: false, error: 'Not found' }, 404);
    return c.json({ success: true, data: item });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** POST /v1/integrations/catalog/seed — admin: seed default catalog */
app.post('/catalog/seed', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Unauthorized' }, 401);
  }
  try {
    const inserted = await seedCatalog(c.env.DB);
    return c.json({ success: true, data: { inserted } });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// ── JWT-protected: install + global events ───────────────────────────────────

/** POST /v1/integrations/install — install integration for tenant */
app.post('/install', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ catalogId: string; config?: Record<string, unknown>; credentials?: Record<string, unknown> }>();
    if (!body.catalogId) return c.json({ success: false, error: 'catalogId required' }, 400);
    const integration = await installIntegration(c.env.DB, tenantId, body);
    return c.json({ success: true, data: integration }, 201);
  } catch (err) {
    const msg = String(err);
    if (msg.includes('UNIQUE')) return c.json({ success: false, error: 'Integration already installed' }, 409);
    return c.json({ success: false, error: msg }, 500);
  }
});

/** GET /v1/integrations/events — all event log for tenant */
app.get('/events', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const { limit } = c.req.query();
    const events = await getEventLog(c.env.DB, tenantId, { limit: limit ? parseInt(limit, 10) : 50 });
    return c.json({ success: true, data: events });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /v1/integrations — list installed integrations */
app.get('/', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const integrations = await getInstalledIntegrations(c.env.DB, tenantId);
    return c.json({ success: true, data: integrations });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// ── JWT-protected: per-integration CRUD + events ─────────────────────────────

/** GET /v1/integrations/:id — get integration details */
app.get('/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const item = await getIntegration(c.env.DB, tenantId, c.req.param('id'));
    if (!item) return c.json({ success: false, error: 'Not found' }, 404);
    return c.json({ success: true, data: item });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** PUT /v1/integrations/:id — update integration config */
app.put('/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ config?: Record<string, unknown>; credentials?: Record<string, unknown>; status?: string }>();
    const updated = await updateIntegration(c.env.DB, tenantId, c.req.param('id'), body);
    if (!updated) return c.json({ success: false, error: 'Not found' }, 404);
    return c.json({ success: true, data: updated });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** DELETE /v1/integrations/:id — uninstall integration */
app.delete('/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const deleted = await uninstallIntegration(c.env.DB, tenantId, c.req.param('id'));
    if (!deleted) return c.json({ success: false, error: 'Not found' }, 404);
    return c.json({ success: true, data: { deleted: true } });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** GET /v1/integrations/:id/events — event log for specific integration */
app.get('/:id/events', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const { limit } = c.req.query();
    const events = await getEventLog(c.env.DB, tenantId, {
      integrationId: c.req.param('id'),
      limit: limit ? parseInt(limit, 10) : 50,
    });
    return c.json({ success: true, data: events });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

/** POST /v1/integrations/:id/events — log event (internal/webhook use) */
app.post('/:id/events', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ eventType: string; direction?: string; payload?: Record<string, unknown>; status?: string; error?: string }>();
    if (!body.eventType) return c.json({ success: false, error: 'eventType required' }, 400);
    await logEvent(c.env.DB, tenantId, c.req.param('id'), body);
    return c.json({ success: true, data: { logged: true } }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export const integrationHub = app;
