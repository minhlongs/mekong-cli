/**
 * Tenant Tag System routes — CRUD for tags and entity associations
 * Auth routes: tenant-scoped (API key)
 * Admin routes: X-Admin-Key protected
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  listTags,
  createTag,
  updateTag,
  deleteTag,
  tagEntity,
  untagEntity,
  getEntityTags,
  findByTag,
  getTagAnalytics,
  getAdminOverview,
} from '../services/tenant-tag-system-service';

const app = new Hono<{ Bindings: Env }>();

// ─── Admin auth middleware ────────────────────────────────────────────────────

function adminAuth() {
  return async (c: any, next: () => Promise<void>) => {
    const key = c.req.header('X-Admin-Key');
    if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
      return json({ error: 'Unauthorized' }, { status: 401 });
    }
    await next();
  };
}

// ─── Tag CRUD ─────────────────────────────────────────────────────────────────

/** GET /tags — list all tags for tenant */
app.get('/tags', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const tags = await listTags(c.env.DB, tenant.tenantId);
    return json({ tags, total: tags.length });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** POST /tags — create a new tag */
app.post('/tags', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{ name: string; color?: string; description?: string }>();
    if (!body.name) return json({ error: 'name is required' }, { status: 400 });
    const tag = await createTag(c.env.DB, tenant.tenantId, body);
    return json({ tag }, { status: 201 });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** PUT /tags/:id — update tag name/color/description */
app.put('/tags/:id', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const { id } = c.req.param();
    const body = await c.req.json<{ name?: string; color?: string; description?: string }>();
    const tag = await updateTag(c.env.DB, tenant.tenantId, id, body);
    if (!tag) return json({ error: 'Tag not found' }, { status: 404 });
    return json({ tag });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** DELETE /tags/:id — delete tag and all associations */
app.delete('/tags/:id', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const { id } = c.req.param();
    await deleteTag(c.env.DB, tenant.tenantId, id);
    return json({ success: true });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

// ─── Entity tag associations ──────────────────────────────────────────────────

/** POST /entities/:entityType/:entityId/tags/:tagId — tag an entity */
app.post('/entities/:entityType/:entityId/tags/:tagId', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const { entityType, entityId, tagId } = c.req.param();
    const association = await tagEntity(c.env.DB, tenant.tenantId, tagId, entityType, entityId);
    return json({ association }, { status: 201 });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** DELETE /entities/:entityType/:entityId/tags/:tagId — remove tag from entity */
app.delete('/entities/:entityType/:entityId/tags/:tagId', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const { entityType, entityId, tagId } = c.req.param();
    await untagEntity(c.env.DB, tenant.tenantId, tagId, entityType, entityId);
    return json({ success: true });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** GET /entities/:entityType/:entityId/tags — list tags on an entity */
app.get('/entities/:entityType/:entityId/tags', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const { entityType, entityId } = c.req.param();
    const tags = await getEntityTags(c.env.DB, tenant.tenantId, entityType, entityId);
    return json({ tags, total: tags.length });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** GET /tags/:id/entities — find entities tagged with a tag */
app.get('/tags/:id/entities', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const { id } = c.req.param();
    const entityType = c.req.query('entityType');
    const entities = await findByTag(c.env.DB, tenant.tenantId, id, entityType);
    return json({ entities, total: entities.length });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

// ─── Analytics ────────────────────────────────────────────────────────────────

/** GET /analytics — tag usage analytics for tenant */
app.get('/analytics', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const analytics = await getTagAnalytics(c.env.DB, tenant.tenantId);
    return json(analytics);
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

/** GET /admin/overview — platform-wide tag overview */
app.get('/admin/overview', adminAuth(), async (c) => {
  try {
    const overview = await getAdminOverview(c.env.DB);
    return json(overview);
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

export { app as tenantTagSystem };
