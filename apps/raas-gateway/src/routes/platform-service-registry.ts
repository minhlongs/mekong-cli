/**
 * Platform Service Registry routes — admin-only (X-Admin-Key)
 * Endpoints: list services, register service, health checks, dashboard summary
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { platformServiceRegistryService } from '../services/platform-service-registry-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth middleware — all routes require X-Admin-Key
app.use('*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden: invalid admin key' }, 403);
  }
  await next();
});

// GET /services — list all registered platform services
app.get('/services', async (c) => {
  try {
    const data = await platformServiceRegistryService.listServices(c.env.DB);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to list services', details: String(err) }, 500);
  }
});

// POST /services — register a new platform service
app.post('/services', async (c) => {
  try {
    const body = await c.req.json();
    const data = await platformServiceRegistryService.registerService(c.env.DB, body);
    return c.json({ ok: true, data }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to register service', details: String(err) }, 500);
  }
});

// GET /health-checks — get health check log (optional ?service_id= filter)
app.get('/health-checks', async (c) => {
  try {
    const serviceId = c.req.query('service_id');
    const data = await platformServiceRegistryService.getHealthChecks(c.env.DB, serviceId);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to get health checks', details: String(err) }, 500);
  }
});

// GET /dashboard — summary counts for platform services + health checks
app.get('/dashboard', async (c) => {
  try {
    const data = await platformServiceRegistryService.getDashboard(c.env.DB);
    return c.json({ ok: true, data });
  } catch (err) {
    return c.json({ error: 'Failed to get dashboard', details: String(err) }, 500);
  }
});

export { app as platformServiceRegistry };
