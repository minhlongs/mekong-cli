/**
 * Project routes — multi-project workspace management per tenant
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const projects = new Hono<{ Bindings: Env }>();
projects.use('*', auth());

/** POST /v1/projects — Create a new project */
projects.post('/', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));

  const name = body.name?.trim();
  if (!name) return json({ error: 'name is required', code: 'INVALID_NAME' }, { status: 400 });
  if (name.length > 100) return json({ error: 'name max 100 chars', code: 'INVALID_NAME' }, { status: 400 });

  const id = crypto.randomUUID();
  const description = body.description?.trim() || null;

  await c.env.DB.prepare(
    'INSERT INTO projects (id, tenant_id, name, description) VALUES (?, ?, ?, ?)'
  ).bind(id, tenant.tenantId, name, description).run();

  const project = await c.env.DB.prepare(
    'SELECT id, name, description, status, created_at FROM projects WHERE id = ?'
  ).bind(id).first();

  return json(project, { status: 201 });
});

/** GET /v1/projects — List all projects for tenant */
projects.get('/', async (c) => {
  const tenant = getTenant(c);

  const result = await c.env.DB.prepare(
    'SELECT * FROM projects WHERE tenant_id = ? AND status != ? ORDER BY created_at DESC'
  ).bind(tenant.tenantId, 'archived').all();

  return json({ projects: result.results, total: result.results.length });
});

/** GET /v1/projects/:id — Get single project with mission stats */
projects.get('/:id', async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');

  const project = await c.env.DB.prepare(
    'SELECT id, name, description, status, mission_count, created_at FROM projects WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenant.tenantId).first();

  if (!project) return json({ error: 'Project not found', code: 'NOT_FOUND' }, { status: 404 });

  return json(project);
});

/** GET /v1/projects/:id/missions — List missions for a project */
projects.get('/:id/missions', async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');

  // Verify project belongs to tenant
  const project = await c.env.DB.prepare(
    'SELECT id FROM projects WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenant.tenantId).first();

  if (!project) return json({ error: 'Project not found', code: 'NOT_FOUND' }, { status: 404 });

  const result = await c.env.DB.prepare(
    'SELECT * FROM missions WHERE tenant_id = ? AND project = ? ORDER BY created_at DESC LIMIT 20'
  ).bind(tenant.tenantId, id).all();

  return json({ missions: result.results, total: result.results.length });
});

/** DELETE /v1/projects/:id — Soft delete (archive) a project */
projects.delete('/:id', async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');

  const project = await c.env.DB.prepare(
    'SELECT id FROM projects WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenant.tenantId).first();

  if (!project) return json({ error: 'Project not found', code: 'NOT_FOUND' }, { status: 404 });

  await c.env.DB.prepare(
    "UPDATE projects SET status = 'archived', updated_at = datetime('now') WHERE id = ?"
  ).bind(id).run();

  return json({ success: true });
});
