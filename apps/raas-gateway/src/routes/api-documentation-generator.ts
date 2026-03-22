/**
 * API Documentation Generator routes
 *
 * Public:  GET /spec/:version
 * Admin:   all other routes (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { apiDocGeneratorService as svc } from '../services/api-documentation-generator-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// ---------------------------------------------------------------------------
// Admin middleware — applies to all routes registered after this point
// Exception: /spec/:version is mounted before the middleware
// ---------------------------------------------------------------------------

/** GET /spec/:version — public, no admin key required */
app.get('/spec/:version', async (c) => {
  try {
    const spec = await svc.generateSpec(c.env.DB, c.req.param('version'));
    return c.json({ success: true, data: spec });
  } catch {
    return c.json({ success: false, error: 'Failed to generate spec' }, 500);
  }
});

// Admin key check middleware for all routes below
app.use('*', async (c, next) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Unauthorized' }, 401);
  }
  return next();
});

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

/** GET /endpoints — list with optional ?tag=&version=&deprecated= */
app.get('/endpoints', async (c) => {
  try {
    const { tag, version, deprecated } = c.req.query() as Record<string, string>;
    const data = await svc.listEndpoints(c.env.DB, { tag, version, deprecated });
    return c.json({ success: true, data });
  } catch {
    return c.json({ success: false, error: 'Failed to list endpoints' }, 500);
  }
});

/** POST /endpoints — create endpoint */
app.post('/endpoints', async (c) => {
  try {
    const body = await c.req.json();
    const data = await svc.createEndpoint(c.env.DB, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to create endpoint';
    return c.json({ success: false, error: msg }, 400);
  }
});

/** GET /endpoints/:id — get single endpoint */
app.get('/endpoints/:id', async (c) => {
  try {
    const data = await svc.getEndpoint(c.env.DB, c.req.param('id'));
    if (!data) return c.json({ success: false, error: 'Not found' }, 404);
    return c.json({ success: true, data });
  } catch {
    return c.json({ success: false, error: 'Failed to get endpoint' }, 500);
  }
});

/** PUT /endpoints/:id — update endpoint */
app.put('/endpoints/:id', async (c) => {
  try {
    const body = await c.req.json();
    const data = await svc.updateEndpoint(c.env.DB, c.req.param('id'), body);
    return c.json({ success: true, data });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to update endpoint';
    return c.json({ success: false, error: msg }, 400);
  }
});

/** DELETE /endpoints/:id — delete endpoint */
app.delete('/endpoints/:id', async (c) => {
  try {
    await svc.deleteEndpoint(c.env.DB, c.req.param('id'));
    return c.json({ success: true });
  } catch {
    return c.json({ success: false, error: 'Failed to delete endpoint' }, 500);
  }
});

// ---------------------------------------------------------------------------
// Examples
// ---------------------------------------------------------------------------

/** GET /endpoints/:id/examples — list code examples for an endpoint */
app.get('/endpoints/:id/examples', async (c) => {
  try {
    const data = await svc.getExamples(c.env.DB, c.req.param('id'));
    return c.json({ success: true, data });
  } catch {
    return c.json({ success: false, error: 'Failed to get examples' }, 500);
  }
});

/** POST /endpoints/:id/examples — add code example */
app.post('/endpoints/:id/examples', async (c) => {
  try {
    const body = await c.req.json();
    const data = await svc.addExample(c.env.DB, c.req.param('id'), body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to add example';
    return c.json({ success: false, error: msg }, 400);
  }
});

// ---------------------------------------------------------------------------
// Versions
// ---------------------------------------------------------------------------

/** GET /versions — list all doc versions */
app.get('/versions', async (c) => {
  try {
    const data = await svc.listVersions(c.env.DB);
    return c.json({ success: true, data });
  } catch {
    return c.json({ success: false, error: 'Failed to list versions' }, 500);
  }
});

/** POST /versions — create a doc version */
app.post('/versions', async (c) => {
  try {
    const body = await c.req.json();
    const data = await svc.createVersion(c.env.DB, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to create version';
    return c.json({ success: false, error: msg }, 400);
  }
});

/** POST /versions/:id/publish — publish a doc version */
app.post('/versions/:id/publish', async (c) => {
  try {
    const data = await svc.publishVersion(c.env.DB, c.req.param('id'));
    return c.json({ success: true, data });
  } catch {
    return c.json({ success: false, error: 'Failed to publish version' }, 500);
  }
});

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

/** GET /dashboard — admin overview stats */
app.get('/dashboard', async (c) => {
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch {
    return c.json({ success: false, error: 'Failed to load dashboard' }, 500);
  }
});

export { app as apiDocGenerator };
