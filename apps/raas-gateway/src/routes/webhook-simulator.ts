/**
 * Webhook Simulator routes — test delivery, inspect payloads, simulate scenarios
 * Auth required on all routes via auth() middleware
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  simulateWebhook,
  listSimulations,
  getSimulation,
  retrySimulation,
  createTestEndpoint,
  listTestEndpoints,
  getEndpointPayloads,
  deleteTestEndpoint,
  getSimulationStats,
  generateSamplePayload,
} from '../services/webhook-simulator-service';

const app = new Hono<{ Bindings: Env }>();
app.use('/*', auth());

/** POST /simulate — run a webhook delivery simulation */
app.post('/simulate', async (c) => {
  const tenant = getTenant(c);
  try {
    const body = await c.req.json<{
      target_url: string;
      event_type: string;
      payload?: Record<string, unknown>;
    }>();
    if (!body.target_url || !body.event_type) {
      return json({ error: 'target_url and event_type are required', code: 'VALIDATION_ERROR' }, { status: 400 });
    }
    const payload = body.payload ?? generateSamplePayload(body.event_type);
    const sim = await simulateWebhook(c.env.DB, tenant.tenantId, body.target_url, body.event_type, payload);
    return json({ simulation: sim }, { status: 201 });
  } catch {
    return json({ error: 'Simulation failed', code: 'SIMULATE_ERROR' }, { status: 500 });
  }
});

/** GET /simulations — list recent simulations */
app.get('/simulations', async (c) => {
  const tenant = getTenant(c);
  try {
    const limit = Math.min(parseInt(c.req.query('limit') ?? '20'), 100);
    const sims = await listSimulations(c.env.DB, tenant.tenantId, limit);
    return json({ simulations: sims, count: sims.length });
  } catch {
    return json({ error: 'Failed to list simulations', code: 'LIST_ERROR' }, { status: 500 });
  }
});

/** GET /stats — aggregate simulation stats */
app.get('/stats', async (c) => {
  const tenant = getTenant(c);
  try {
    const stats = await getSimulationStats(c.env.DB, tenant.tenantId);
    return json({ stats });
  } catch {
    return json({ error: 'Failed to get stats', code: 'STATS_ERROR' }, { status: 500 });
  }
});

/** GET /sample/:eventType — get sample payload for event type */
app.get('/sample/:eventType', (c) => {
  const eventType = c.req.param('eventType');
  const payload = generateSamplePayload(eventType);
  return json({ event_type: eventType, payload });
});

/** GET /simulations/:id — get single simulation detail */
app.get('/simulations/:id', async (c) => {
  const tenant = getTenant(c);
  try {
    const sim = await getSimulation(c.env.DB, c.req.param('id'), tenant.tenantId);
    if (!sim) return json({ error: 'Simulation not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ simulation: sim });
  } catch {
    return json({ error: 'Failed to get simulation', code: 'GET_ERROR' }, { status: 500 });
  }
});

/** POST /simulations/:id/retry — retry a failed simulation */
app.post('/simulations/:id/retry', async (c) => {
  const tenant = getTenant(c);
  try {
    const sim = await retrySimulation(c.env.DB, c.req.param('id'), tenant.tenantId);
    if (!sim) return json({ error: 'Simulation not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ simulation: sim });
  } catch {
    return json({ error: 'Retry failed', code: 'RETRY_ERROR' }, { status: 500 });
  }
});

/** POST /test-endpoints — create a captive test endpoint */
app.post('/test-endpoints', async (c) => {
  const tenant = getTenant(c);
  try {
    const endpoint = await createTestEndpoint(c.env.DB, tenant.tenantId);
    return json({ endpoint }, { status: 201 });
  } catch {
    return json({ error: 'Failed to create test endpoint', code: 'CREATE_ERROR' }, { status: 500 });
  }
});

/** GET /test-endpoints — list test endpoints */
app.get('/test-endpoints', async (c) => {
  const tenant = getTenant(c);
  try {
    const endpoints = await listTestEndpoints(c.env.DB, tenant.tenantId);
    return json({ endpoints, count: endpoints.length });
  } catch {
    return json({ error: 'Failed to list endpoints', code: 'LIST_ERROR' }, { status: 500 });
  }
});

/** GET /test-endpoints/:id — get endpoint + received payloads */
app.get('/test-endpoints/:id', async (c) => {
  const tenant = getTenant(c);
  try {
    const endpoint = await getEndpointPayloads(c.env.DB, c.req.param('id'), tenant.tenantId);
    if (!endpoint) return json({ error: 'Endpoint not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ endpoint });
  } catch {
    return json({ error: 'Failed to get endpoint', code: 'GET_ERROR' }, { status: 500 });
  }
});

/** DELETE /test-endpoints/:id — remove test endpoint */
app.delete('/test-endpoints/:id', async (c) => {
  const tenant = getTenant(c);
  try {
    const deleted = await deleteTestEndpoint(c.env.DB, c.req.param('id'), tenant.tenantId);
    if (!deleted) return json({ error: 'Endpoint not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ deleted: true });
  } catch {
    return json({ error: 'Failed to delete endpoint', code: 'DELETE_ERROR' }, { status: 500 });
  }
});

export { app as webhookSimulator };
