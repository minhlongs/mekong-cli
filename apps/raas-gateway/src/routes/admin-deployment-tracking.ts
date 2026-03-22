/**
 * Admin Deployment Tracking routes — deployment records and rollback tracking
 * All endpoints require X-Admin-Key header. Mount path: /admin/deployment-tracking
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { adminDeploymentTrackingService } from '../services/admin-deployment-tracking-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /deployments — list deployments with optional ?environment= &status= &limit=
app.get('/deployments', async (c) => {
  try {
    const environment = c.req.query('environment');
    const status = c.req.query('status');
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const deployments = await adminDeploymentTrackingService.listDeployments(c.env.DB, { environment, status, limit });
    return c.json({ deployments, count: deployments.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /deployments — create a new deployment record
app.post('/deployments', async (c) => {
  try {
    const body = await c.req.json<{
      version: string;
      environment?: string;
      deploy_type?: string;
      deployed_by?: string;
      commit_hash?: string;
      changelog?: string;
    }>();
    if (!body.version) return c.json({ error: 'version is required' }, 400);
    const deployment = await adminDeploymentTrackingService.createDeployment(c.env.DB, body);
    return c.json(deployment, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /rollbacks — list rollbacks with optional ?deployment_id= &limit=
app.get('/rollbacks', async (c) => {
  try {
    const deployment_id = c.req.query('deployment_id');
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const rollbacks = await adminDeploymentTrackingService.getRollbacks(c.env.DB, { deployment_id, limit });
    return c.json({ rollbacks, count: rollbacks.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — deployment summary counts
app.get('/dashboard', async (c) => {
  try {
    const summary = await adminDeploymentTrackingService.getDashboard(c.env.DB);
    return c.json(summary);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminDeploymentTracking };
