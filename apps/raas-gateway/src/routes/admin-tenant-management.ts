/**
 * Admin Tenant Management routes — notes, tags, risk scores per tenant
 * All endpoints require X-Admin-Key header
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  addNote,
  listNotes,
  deleteNote,
  addTag,
  listTags,
  removeTag,
  calculateRiskScore,
  getRiskScore,
  listAtRiskTenants,
  getAdminTenantDashboard,
} from '../services/admin-tenant-management-service';

export const adminTenantManagement = new Hono<{ Bindings: Env }>();

// Admin auth guard
adminTenantManagement.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Unauthorized' }, 401);
  await next();
});

// GET /tenants/:tenantId/notes — list notes
adminTenantManagement.get('/tenants/:tenantId/notes', async (c) => {
  try {
    const noteType = c.req.query('noteType');
    const notes = await listNotes(c.env.DB, c.req.param('tenantId'), noteType);
    return json({ notes, count: notes.length });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// POST /tenants/:tenantId/notes — add note
adminTenantManagement.post('/tenants/:tenantId/notes', async (c) => {
  try {
    const body = await c.req.json<{
      author?: string;
      content: string;
      noteType?: string;
      isPinned?: boolean;
    }>();

    if (!body.content) return json({ error: 'content is required' }, { status: 400 });

    const note = await addNote(
      c.env.DB,
      c.req.param('tenantId'),
      body.author ?? 'admin',
      body.content,
      body.noteType ?? 'general',
      body.isPinned ?? false
    );
    return json(note, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// DELETE /tenants/:tenantId/notes/:noteId — delete note
adminTenantManagement.delete('/tenants/:tenantId/notes/:noteId', async (c) => {
  try {
    const deleted = await deleteNote(c.env.DB, c.req.param('tenantId'), c.req.param('noteId'));
    if (!deleted) return json({ error: 'Note not found' }, { status: 404 });
    return json({ deleted: true });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /tenants/:tenantId/tags — list tags
adminTenantManagement.get('/tenants/:tenantId/tags', async (c) => {
  try {
    const tags = await listTags(c.env.DB, c.req.param('tenantId'));
    return json({ tags, count: tags.length });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// POST /tenants/:tenantId/tags — add tag
adminTenantManagement.post('/tenants/:tenantId/tags', async (c) => {
  try {
    const body = await c.req.json<{ tag: string; color?: string }>();
    if (!body.tag) return json({ error: 'tag is required' }, { status: 400 });

    const tag = await addTag(c.env.DB, c.req.param('tenantId'), body.tag, body.color);
    return json(tag, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// DELETE /tenants/:tenantId/tags/:tagId — remove tag
adminTenantManagement.delete('/tenants/:tenantId/tags/:tagId', async (c) => {
  try {
    const removed = await removeTag(c.env.DB, c.req.param('tenantId'), c.req.param('tagId'));
    if (!removed) return json({ error: 'Tag not found' }, { status: 404 });
    return json({ deleted: true });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /tenants/:tenantId/risk — get risk score
adminTenantManagement.get('/tenants/:tenantId/risk', async (c) => {
  try {
    const score = await getRiskScore(c.env.DB, c.req.param('tenantId'));
    if (!score) return json({ error: 'Risk score not yet calculated' }, { status: 404 });
    return json(score);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// POST /tenants/:tenantId/risk/calculate — recalculate risk
adminTenantManagement.post('/tenants/:tenantId/risk/calculate', async (c) => {
  try {
    const score = await calculateRiskScore(c.env.DB, c.req.param('tenantId'));
    return json(score);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /at-risk — list at-risk tenants
adminTenantManagement.get('/at-risk', async (c) => {
  try {
    const threshold = parseFloat(c.req.query('threshold') ?? '50');
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const tenants = await listAtRiskTenants(c.env.DB, threshold, limit);
    return json({ tenants, count: tenants.length, threshold });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// GET /dashboard — admin tenant dashboard
adminTenantManagement.get('/dashboard', async (c) => {
  try {
    const dashboard = await getAdminTenantDashboard(c.env.DB);
    return json(dashboard);
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});
