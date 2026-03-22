/**
 * Mission Template Library routes
 * GET/POST /templates — list, create (auth)
 * GET/PUT/DELETE /templates/:id — read, update, delete (auth)
 * GET /categories — list categories (public)
 * POST /templates/:id/instantiate — clone from template (auth)
 * GET /templates/:id/versions — version history (auth)
 * GET /admin/overview — admin stats (admin key)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { missionTemplateLibraryService as svc } from '../services/mission-template-library-service';

const app = new Hono<{
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
}>();

// ─── AUTH MIDDLEWARE ──────────────────────────────────────────────────────────

const requireAuth = auth();

// ─── PUBLIC ──────────────────────────────────────────────────────────────────

/** GET /categories — no auth required */
app.get('/categories', async (c) => {
  try {
    const categories = await svc.listCategories(c.env.DB);
    return json({ categories });
  } catch {
    return json({ error: 'Failed to fetch categories' }, { status: 500 });
  }
});

// ─── ADMIN ───────────────────────────────────────────────────────────────────

/** GET /admin/overview — admin API key required */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return json(overview);
  } catch {
    return json({ error: 'Failed to fetch overview' }, { status: 500 });
  }
});

// ─── AUTH ROUTES ─────────────────────────────────────────────────────────────

/** GET /templates — list templates for tenant (paginated, filterable) */
app.get('/templates', requireAuth, async (c) => {
  const tenant = getTenant(c);
  const limit = Math.min(parseInt(c.req.query('limit') || '20'), 100);
  const offset = parseInt(c.req.query('offset') || '0');
  const category = c.req.query('category');
  const is_public = c.req.query('is_public');
  try {
    const result = await svc.listTemplates(c.env.DB, tenant.tenantId, {
      limit,
      offset,
      category: category || undefined,
      is_public: is_public !== undefined ? is_public === 'true' : undefined,
    });
    return json(result);
  } catch {
    return json({ error: 'Failed to list templates' }, { status: 500 });
  }
});

/** POST /templates — create new template */
app.post('/templates', requireAuth, async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  if (!body.name || typeof body.name !== 'string') {
    return json({ error: 'name is required' }, { status: 400 });
  }
  try {
    const result = await svc.createTemplate(c.env.DB, tenant.tenantId, {
      name: body.name,
      description: typeof body.description === 'string' ? body.description : undefined,
      category: typeof body.category === 'string' ? body.category : undefined,
      config_json: typeof body.config_json === 'string' ? body.config_json : undefined,
      parameters_json: typeof body.parameters_json === 'string' ? body.parameters_json : undefined,
      is_public: typeof body.is_public === 'boolean' ? body.is_public : false,
    });
    return json(result, { status: 201 });
  } catch {
    return json({ error: 'Failed to create template' }, { status: 500 });
  }
});

/** GET /templates/:id — fetch single template */
app.get('/templates/:id', requireAuth, async (c) => {
  const tenant = getTenant(c);
  try {
    const tpl = await svc.getTemplate(c.env.DB, tenant.tenantId, c.req.param('id'));
    if (!tpl) return json({ error: 'Template not found' }, { status: 404 });
    return json(tpl);
  } catch {
    return json({ error: 'Failed to fetch template' }, { status: 500 });
  }
});

/** PUT /templates/:id — update template (bumps version) */
app.put('/templates/:id', requireAuth, async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  try {
    const result = await svc.updateTemplate(c.env.DB, tenant.tenantId, c.req.param('id'), {
      name: typeof body.name === 'string' ? body.name : undefined,
      description: typeof body.description === 'string' ? body.description : undefined,
      category: typeof body.category === 'string' ? body.category : undefined,
      config_json: typeof body.config_json === 'string' ? body.config_json : undefined,
      parameters_json: typeof body.parameters_json === 'string' ? body.parameters_json : undefined,
      is_public: typeof body.is_public === 'boolean' ? body.is_public : undefined,
      changelog: typeof body.changelog === 'string' ? body.changelog : undefined,
    });
    if (!result) return json({ error: 'Template not found' }, { status: 404 });
    return json(result);
  } catch {
    return json({ error: 'Failed to update template' }, { status: 500 });
  }
});

/** DELETE /templates/:id — delete template */
app.delete('/templates/:id', requireAuth, async (c) => {
  const tenant = getTenant(c);
  try {
    const deleted = await svc.deleteTemplate(c.env.DB, tenant.tenantId, c.req.param('id'));
    if (!deleted) return json({ error: 'Template not found' }, { status: 404 });
    return json({ deleted: true });
  } catch {
    return json({ error: 'Failed to delete template' }, { status: 500 });
  }
});

/** POST /templates/:id/instantiate — clone template with overrides */
app.post('/templates/:id/instantiate', requireAuth, async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  try {
    const result = await svc.createFromTemplate(c.env.DB, tenant.tenantId, c.req.param('id'), {
      name: typeof body.name === 'string' ? body.name : undefined,
      description: typeof body.description === 'string' ? body.description : undefined,
      config_json: typeof body.config_json === 'string' ? body.config_json : undefined,
    });
    if (!result) return json({ error: 'Template not found' }, { status: 404 });
    return json(result, { status: 201 });
  } catch {
    return json({ error: 'Failed to instantiate template' }, { status: 500 });
  }
});

/** GET /templates/:id/versions — list version history */
app.get('/templates/:id/versions', requireAuth, async (c) => {
  try {
    const versions = await svc.listVersions(c.env.DB, c.req.param('id'));
    return json({ versions });
  } catch {
    return json({ error: 'Failed to fetch versions' }, { status: 500 });
  }
});

export { app as missionTemplateLibrary };
