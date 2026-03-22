/**
 * Mission Retry Policies routes — configure retry behavior and track attempts
 * Auth endpoints require JWT/API-key. Admin endpoint requires X-Admin-Key.
 * Mount path: /v1/mission-retry-policies
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import * as svc from '../services/mission-retry-policies';

const app = new Hono<{ Bindings: Env }>();

// GET /policies — list retry policies for tenant
app.get('/policies', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listPolicies(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /policies — create a new retry policy
app.post('/policies', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      policy_name: string;
      max_retries?: number;
      backoff_type?: string;
      initial_delay_ms?: number;
      max_delay_ms?: number;
    }>();
    if (!body.policy_name) return c.json({ error: 'policy_name is required' }, 400);
    const data = await svc.createPolicy(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /attempts — list retry attempts for tenant
app.get('/attempts', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.getAttempts(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — admin stats across all tenants (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as missionRetryPolicies };
