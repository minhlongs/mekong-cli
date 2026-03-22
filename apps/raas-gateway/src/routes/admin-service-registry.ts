/**
 * Admin Service Registry routes
 * All endpoints protected by X-Admin-Key header (403 on failure)
 * Mount at: /admin/service-registry
 */

import { Hono } from 'hono';
import { adminServiceRegistryService } from '../services/admin-service-registry';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin-only guard — 403 on missing or wrong key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /admin/service-registry/services — list all services, optional ?status= filter
app.get('/services', async (c) => {
  try {
    const status = c.req.query('status');
    const result = await adminServiceRegistryService.listServices(c.env.DB, status);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// POST /admin/service-registry/services — register a new service
app.post('/services', async (c) => {
  try {
    const body = await c.req.json();
    const { id, service_name, service_url, health_endpoint, status, version } = body;

    if (!id || !service_name || !service_url) {
      return c.json({ error: 'id, service_name, and service_url are required' }, 400);
    }

    const result = await adminServiceRegistryService.createService(c.env.DB, {
      id,
      service_name,
      service_url,
      health_endpoint,
      status,
      version,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /admin/service-registry/dependencies?service_id= — fetch dependency edges
app.get('/dependencies', async (c) => {
  try {
    const serviceId = c.req.query('service_id');
    if (!serviceId) {
      return c.json({ error: 'service_id query param is required' }, 400);
    }

    const result = await adminServiceRegistryService.getDependencies(c.env.DB, serviceId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// GET /admin/service-registry/dashboard — aggregated health overview
app.get('/dashboard', async (c) => {
  try {
    const result = await adminServiceRegistryService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as adminServiceRegistry };
