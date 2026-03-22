/**
 * Tenant Custom Fields routes
 * Mount at: /v1/custom-fields
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantCustomFieldsService as svc } from '../services/tenant-custom-fields-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// --- Field Definitions ---

/** GET /definitions — list definitions for tenant, optional ?entity_type filter */
app.get('/definitions', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const entityType = c.req.query('entity_type');
    const data = await svc.listDefinitions(c.env.DB, tenantId, entityType);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-fields GET /definitions]', err);
    return c.json({ success: false, error: 'Failed to list definitions' }, 500);
  }
});

/** POST /definitions — create a new field definition */
app.post('/definitions', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.entity_type || !body.field_name || !body.label) {
      return c.json({ success: false, error: 'entity_type, field_name, and label are required' }, 400);
    }
    const data = await svc.createDefinition(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    console.error('[custom-fields POST /definitions]', err);
    return c.json({ success: false, error: 'Failed to create definition' }, 500);
  }
});

/** GET /definitions/:id — get single definition */
app.get('/definitions/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.getDefinition(c.env.DB, tenantId, c.req.param('id'));
    if (!data) return c.json({ success: false, error: 'Definition not found' }, 404);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-fields GET /definitions/:id]', err);
    return c.json({ success: false, error: 'Failed to get definition' }, 500);
  }
});

/** PUT /definitions/:id — update definition */
app.put('/definitions/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    const data = await svc.updateDefinition(c.env.DB, tenantId, c.req.param('id'), body);
    if (!data) return c.json({ success: false, error: 'Definition not found' }, 404);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-fields PUT /definitions/:id]', err);
    return c.json({ success: false, error: 'Failed to update definition' }, 500);
  }
});

/** DELETE /definitions/:id — delete definition and its values */
app.delete('/definitions/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const deleted = await svc.deleteDefinition(c.env.DB, tenantId, c.req.param('id'));
    if (!deleted) return c.json({ success: false, error: 'Definition not found' }, 404);
    return c.json({ success: true, message: 'Definition deleted' });
  } catch (err) {
    console.error('[custom-fields DELETE /definitions/:id]', err);
    return c.json({ success: false, error: 'Failed to delete definition' }, 500);
  }
});

// --- Field Values ---

/** GET /values/:entityId — get all field values for an entity */
app.get('/values/:entityId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.getValues(c.env.DB, tenantId, c.req.param('entityId'));
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-fields GET /values/:entityId]', err);
    return c.json({ success: false, error: 'Failed to get values' }, 500);
  }
});

/** PUT /values/:entityId/:definitionId — set single field value */
app.put('/values/:entityId/:definitionId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    const data = await svc.setValue(
      c.env.DB, tenantId,
      c.req.param('entityId'),
      c.req.param('definitionId'),
      body.value,
    );
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-fields PUT /values/:entityId/:definitionId]', err);
    return c.json({ success: false, error: 'Failed to set value' }, 500);
  }
});

/** POST /values/:entityId/bulk — set multiple field values at once */
app.post('/values/:entityId/bulk', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.values || typeof body.values !== 'object') {
      return c.json({ success: false, error: 'values object is required' }, 400);
    }
    const data = await svc.bulkSetValues(c.env.DB, tenantId, c.req.param('entityId'), body.values);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-fields POST /values/:entityId/bulk]', err);
    return c.json({ success: false, error: 'Failed to bulk set values' }, 500);
  }
});

// --- Search ---

/** GET /search — search entities by field value (?definition_id=&value=) */
app.get('/search', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const definitionId = c.req.query('definition_id');
    const value = c.req.query('value');
    if (!definitionId || !value) {
      return c.json({ success: false, error: 'definition_id and value query params required' }, 400);
    }
    const data = await svc.searchByField(c.env.DB, tenantId, definitionId, value);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-fields GET /search]', err);
    return c.json({ success: false, error: 'Failed to search' }, 500);
  }
});

// --- Admin ---

/** GET /admin/overview — platform-wide stats (admin key required) */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ success: false, error: 'Invalid admin key' }, 401);
    }
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[custom-fields GET /admin/overview]', err);
    return c.json({ success: false, error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantCustomFields };
