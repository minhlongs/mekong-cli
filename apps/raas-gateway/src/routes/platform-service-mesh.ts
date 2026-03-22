/**
 * Platform Service Mesh routes — admin-only (X-Admin-Key)
 * Endpoints: service registry CRUD, health check, circuit breaker, traffic rules, topology, dashboard
 */

import { Hono } from 'hono';
import { platformServiceMeshService } from '../services/platform-service-mesh-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// Admin auth middleware — all routes require X-Admin-Key
app.use('*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden: invalid admin key' }, 403);
  }
  await next();
});

// GET /services — list all registered services
app.get('/services', async (c) => {
  try {
    const data = await platformServiceMeshService.listServices(c.env.DB);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to list services', details: String(err) }, 500);
  }
});

// POST /services — register a new service
app.post('/services', async (c) => {
  try {
    const body = await c.req.json();
    const data = await platformServiceMeshService.registerService(c.env.DB, body);
    return c.json({ ok: true, data }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to register service', details: String(err) }, 500);
  }
});

// GET /services/:id — get a single service
app.get('/services/:id', async (c) => {
  try {
    const data = await platformServiceMeshService.getService(c.env.DB, c.req.param('id'));
    if (!data) return c.json({ error: 'Service not found' }, 404);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to get service', details: String(err) }, 500);
  }
});

// PUT /services/:id — update service fields
app.put('/services/:id', async (c) => {
  try {
    const body = await c.req.json();
    const data = await platformServiceMeshService.updateService(c.env.DB, c.req.param('id'), body);
    if (!data) return c.json({ error: 'Service not found' }, 404);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to update service', details: String(err) }, 500);
  }
});

// DELETE /services/:id — deregister service
app.delete('/services/:id', async (c) => {
  try {
    const data = await platformServiceMeshService.deregisterService(c.env.DB, c.req.param('id'));
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to deregister service', details: String(err) }, 500);
  }
});

// POST /services/:id/health — run health check
app.post('/services/:id/health', async (c) => {
  try {
    const data = await platformServiceMeshService.healthCheck(c.env.DB, c.req.param('id'));
    if (!data) return c.json({ error: 'Service not found' }, 404);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to run health check', details: String(err) }, 500);
  }
});

// GET /services/:id/circuit-breaker — get circuit breaker config
app.get('/services/:id/circuit-breaker', async (c) => {
  try {
    const data = await platformServiceMeshService.getCircuitBreaker(c.env.DB, c.req.param('id'));
    if (!data) return c.json({ error: 'Circuit breaker not found' }, 404);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to get circuit breaker', details: String(err) }, 500);
  }
});

// PUT /services/:id/circuit-breaker — upsert circuit breaker config
app.put('/services/:id/circuit-breaker', async (c) => {
  try {
    const body = await c.req.json();
    const data = await platformServiceMeshService.updateCircuitBreaker(c.env.DB, c.req.param('id'), body);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to update circuit breaker', details: String(err) }, 500);
  }
});

// GET /traffic-rules — list all traffic rules
app.get('/traffic-rules', async (c) => {
  try {
    const data = await platformServiceMeshService.listTrafficRules(c.env.DB);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to list traffic rules', details: String(err) }, 500);
  }
});

// POST /traffic-rules — create a traffic rule
app.post('/traffic-rules', async (c) => {
  try {
    const body = await c.req.json();
    const data = await platformServiceMeshService.createTrafficRule(c.env.DB, body);
    return c.json({ ok: true, data }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create traffic rule', details: String(err) }, 500);
  }
});

// GET /topology — mesh topology: services + connections
app.get('/topology', async (c) => {
  try {
    const data = await platformServiceMeshService.getMeshTopology(c.env.DB);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to get topology', details: String(err) }, 500);
  }
});

// GET /dashboard — admin overview: counts + health stats
app.get('/dashboard', async (c) => {
  try {
    const data = await platformServiceMeshService.getAdminOverview(c.env.DB);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to get dashboard', details: String(err) }, 500);
  }
});

export { app as platformServiceMesh };
