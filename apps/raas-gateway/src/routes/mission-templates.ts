/**
 * Mission Templates — library + marketplace listing
 * PUBLIC: marketplaceTemplates (/marketplace/templates)
 * AUTH:   missionTemplates     (/v1/templates)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

const VALID_CATEGORIES = [
  'seo-audit', 'content-generation', 'code-review', 'data-analysis',
  'social-media', 'email-marketing', 'research', 'custom',
] as const;

const TPL_SELECT = `SELECT id, name, slug, description, category, goal_template,
  default_model, estimated_credits, usage_count,
  CASE WHEN rating_count > 0 THEN ROUND(CAST(rating_sum AS REAL)/rating_count,1) ELSE NULL END as avg_rating,
  rating_count, created_at FROM mission_templates`;

// ─── PUBLIC ──────────────────────────────────────────────────────────────────
export const marketplaceTemplates = new Hono<{ Bindings: Env }>();

marketplaceTemplates.get('/', async (c) => {
  const limit = Math.min(parseInt(c.req.query('limit') || '20'), 50);
  const offset = parseInt(c.req.query('offset') || '0');
  const category = c.req.query('category');
  const bindings: (string | number)[] = category ? [category] : [];
  const where = 'WHERE is_public = 1' + (category ? ' AND category = ?' : '');
  try {
    const [rows, cnt] = await Promise.all([
      c.env.DB.prepare(`${TPL_SELECT} ${where} ORDER BY usage_count DESC LIMIT ? OFFSET ?`)
        .bind(...bindings, limit, offset).all(),
      c.env.DB.prepare(`SELECT COUNT(*) as total FROM mission_templates ${where}`)
        .bind(...bindings).first<{ total: number }>(),
    ]);
    return json({ templates: rows.results, total: cnt?.total || 0, pagination: { limit, offset } });
  } catch { return json({ error: 'Failed to fetch templates' }, { status: 500 }); }
});

marketplaceTemplates.get('/:slug', async (c) => {
  try {
    const tpl = await c.env.DB.prepare(`${TPL_SELECT} WHERE slug = ? AND is_public = 1`)
      .bind(c.req.param('slug')).first();
    return tpl ? json(tpl) : json({ error: 'Template not found' }, { status: 404 });
  } catch { return json({ error: 'Failed to fetch template' }, { status: 500 }); }
});

// ─── AUTH ─────────────────────────────────────────────────────────────────────
export const missionTemplates = new Hono<{ Bindings: Env }>();

missionTemplates.post('/', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch { return json({ error: 'Invalid JSON' }, { status: 400 }); }
  const { name, slug, description, category, goal_template, default_model, estimated_credits, is_public } = body;
  if (!name || !slug || !category || !goal_template)
    return json({ error: 'name, slug, category, goal_template are required' }, { status: 400 });
  if (!VALID_CATEGORIES.includes(category as typeof VALID_CATEGORIES[number]))
    return json({ error: `category must be one of: ${VALID_CATEGORIES.join(', ')}` }, { status: 400 });
  const id = crypto.randomUUID();
  try {
    await c.env.DB.prepare(
      `INSERT INTO mission_templates (id, name, slug, description, category, goal_template, default_model, estimated_credits, is_public, creator_tenant_id)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, name, slug, description ?? null, category, goal_template,
      default_model ?? 'auto', estimated_credits ?? 1, is_public ? 1 : 0, tenant.tenantId).run();
    return json({ id, name, slug, category, goal_template }, { status: 201 });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '';
    if (msg.includes('UNIQUE')) return json({ error: 'Slug already exists' }, { status: 409 });
    return json({ error: 'Failed to create template' }, { status: 500 });
  }
});

missionTemplates.get('/', auth(), async (c) => {
  const tenant = getTenant(c);
  const limit = Math.min(parseInt(c.req.query('limit') || '20'), 50);
  const offset = parseInt(c.req.query('offset') || '0');
  try {
    const rows = await c.env.DB.prepare(
      `SELECT id, name, slug, category, goal_template, estimated_credits, is_public, usage_count, creator_tenant_id, created_at
       FROM mission_templates WHERE is_public = 1 OR creator_tenant_id = ?
       ORDER BY created_at DESC LIMIT ? OFFSET ?`
    ).bind(tenant.tenantId, limit, offset).all();
    return json({ templates: rows.results, pagination: { limit, offset } });
  } catch { return json({ error: 'Failed to list templates' }, { status: 500 }); }
});

missionTemplates.get('/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const tpl = await c.env.DB.prepare(
      'SELECT * FROM mission_templates WHERE id = ? AND (is_public = 1 OR creator_tenant_id = ?)'
    ).bind(c.req.param('id'), tenant.tenantId).first();
    return tpl ? json(tpl) : json({ error: 'Template not found' }, { status: 404 });
  } catch { return json({ error: 'Failed to fetch template' }, { status: 500 }); }
});

missionTemplates.put('/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch { return json({ error: 'Invalid JSON' }, { status: 400 }); }
  const existing = await c.env.DB.prepare(
    'SELECT id FROM mission_templates WHERE id = ? AND creator_tenant_id = ?'
  ).bind(id, tenant.tenantId).first();
  if (!existing) return json({ error: 'Template not found or not owned by you' }, { status: 404 });
  const { name, description, category, goal_template, default_model, estimated_credits, is_public } = body;
  try {
    await c.env.DB.prepare(
      `UPDATE mission_templates SET
        name = COALESCE(?, name), description = COALESCE(?, description),
        category = COALESCE(?, category), goal_template = COALESCE(?, goal_template),
        default_model = COALESCE(?, default_model), estimated_credits = COALESCE(?, estimated_credits),
        is_public = COALESCE(?, is_public), updated_at = datetime('now') WHERE id = ?`
    ).bind(name ?? null, description ?? null, category ?? null, goal_template ?? null,
      default_model ?? null, estimated_credits ?? null,
      is_public !== undefined ? (is_public ? 1 : 0) : null, id).run();
    return json({ id, updated: true });
  } catch { return json({ error: 'Failed to update template' }, { status: 500 }); }
});

missionTemplates.delete('/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const result = await c.env.DB.prepare(
      'DELETE FROM mission_templates WHERE id = ? AND creator_tenant_id = ?'
    ).bind(c.req.param('id'), tenant.tenantId).run();
    if (!result.meta.changes) return json({ error: 'Template not found or not owned by you' }, { status: 404 });
    return json({ id: c.req.param('id'), deleted: true });
  } catch { return json({ error: 'Failed to delete template' }, { status: 500 }); }
});

missionTemplates.post('/:id/use', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch { body = {}; }
  try {
    const tpl = await c.env.DB.prepare(
      'SELECT goal_template, default_model, estimated_credits FROM mission_templates WHERE id = ? AND (is_public = 1 OR creator_tenant_id = ?)'
    ).bind(id, tenant.tenantId).first<{ goal_template: string; default_model: string; estimated_credits: number }>();
    if (!tpl) return json({ error: 'Template not found' }, { status: 404 });
    let goal = tpl.goal_template;
    for (const [k, v] of Object.entries(body)) goal = goal.replaceAll(`{${k}}`, String(v));
    await c.env.DB.prepare('UPDATE mission_templates SET usage_count = usage_count + 1 WHERE id = ?').bind(id).run();
    return json({ templateId: id, goal, model: tpl.default_model, estimated_credits: tpl.estimated_credits });
  } catch { return json({ error: 'Failed to use template' }, { status: 500 }); }
});

missionTemplates.post('/:id/rate', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch { return json({ error: 'Invalid JSON' }, { status: 400 }); }
  const rating = Number(body.rating);
  if (!Number.isInteger(rating) || rating < 1 || rating > 5)
    return json({ error: 'rating must be an integer between 1 and 5' }, { status: 400 });
  try {
    const tpl = await c.env.DB.prepare(
      'SELECT id FROM mission_templates WHERE id = ? AND (is_public = 1 OR creator_tenant_id = ?)'
    ).bind(id, tenant.tenantId).first();
    if (!tpl) return json({ error: 'Template not found' }, { status: 404 });
    await c.env.DB.prepare(
      `UPDATE mission_templates SET rating_sum = rating_sum + ?, rating_count = rating_count + 1, updated_at = datetime('now') WHERE id = ?`
    ).bind(rating, id).run();
    return json({ templateId: id, rated: rating });
  } catch { return json({ error: 'Failed to rate template' }, { status: 500 }); }
});
