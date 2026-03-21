/**
 * Environment routes — CRUD, variable management, clone, and seed endpoints
 * Mounted at /v1/environments in parent router
 * IMPORTANT: /seed mounted BEFORE /:id to avoid route shadowing
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createEnvironment,
  getEnvironments,
  getEnvironment,
  updateEnvironment,
  deleteEnvironment,
  setVariable,
  getVariables,
  deleteVariable,
  cloneEnvironment,
  seedDefaultEnvironments,
  type EnvType,
} from '../services/environment-service';

const app = new Hono<{ Bindings: Env }>();

// Apply auth to all routes
app.use('/*', auth());

// GET / — list all environments
app.get('/', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const envs = await getEnvironments(c.env.DB, tenantId);
    return c.json({ success: true, data: envs });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST / — create environment
app.post('/', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      name: string;
      envType: EnvType;
      description?: string;
      config?: Record<string, unknown>;
      apiBaseUrl?: string;
    }>();
    if (!body.name || !body.envType) {
      return c.json({ success: false, error: 'name and envType are required' }, 400);
    }
    const env = await createEnvironment(c.env.DB, tenantId, body);
    return c.json({ success: true, data: env }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /seed — seed default production + staging (BEFORE /:id)
app.post('/seed', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const envs = await seedDefaultEnvironments(c.env.DB, tenantId);
    return c.json({ success: true, data: envs });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /:id — get single environment
app.get('/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const env = await getEnvironment(c.env.DB, tenantId, c.req.param('id'));
    if (!env) return c.json({ success: false, error: 'Environment not found' }, 404);
    return c.json({ success: true, data: env });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// PUT /:id — update environment
app.put('/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      name?: string;
      description?: string;
      config?: Record<string, unknown>;
      apiBaseUrl?: string;
      isActive?: boolean;
    }>();
    const env = await updateEnvironment(c.env.DB, tenantId, c.req.param('id'), body);
    if (!env) return c.json({ success: false, error: 'Environment not found' }, 404);
    return c.json({ success: true, data: env });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// DELETE /:id — delete environment (blocks production)
app.delete('/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await deleteEnvironment(c.env.DB, tenantId, c.req.param('id'));
    if (!result.deleted) {
      const status = result.error === 'Not found' ? 404 : 400;
      return c.json({ success: false, error: result.error }, status);
    }
    return c.json({ success: true, data: { deleted: true } });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /:id/clone — clone environment
app.post('/:id/clone', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ name: string; envType: EnvType }>();
    if (!body.name || !body.envType) {
      return c.json({ success: false, error: 'name and envType are required' }, 400);
    }
    const env = await cloneEnvironment(c.env.DB, tenantId, c.req.param('id'), body.name, body.envType);
    return c.json({ success: true, data: env }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /:id/variables — list variables (secrets masked)
app.get('/:id/variables', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const vars = await getVariables(c.env.DB, tenantId, c.req.param('id'));
    return c.json({ success: true, data: vars });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// PUT /:id/variables/:key — upsert variable
app.put('/:id/variables/:key', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ value: string; isSecret?: boolean }>();
    if (body.value === undefined) {
      return c.json({ success: false, error: 'value is required' }, 400);
    }
    const variable = await setVariable(
      c.env.DB, tenantId, c.req.param('id'),
      c.req.param('key'), body.value, body.isSecret ?? false
    );
    return c.json({ success: true, data: variable });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// DELETE /:id/variables/:key — delete variable
app.delete('/:id/variables/:key', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const deleted = await deleteVariable(c.env.DB, tenantId, c.req.param('id'), c.req.param('key'));
    if (!deleted) return c.json({ success: false, error: 'Variable not found' }, 404);
    return c.json({ success: true, data: { deleted: true } });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export const environments = app;
