/**
 * Admin Deployment Manager routes — deployment lifecycle, checks, canary management
 * All endpoints require X-Admin-Key header. Mount path: /admin/deployments
 */

import { Hono } from 'hono';
import { adminDeploymentManagerService } from '../services/admin-deployment-manager-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /deployments — list with optional ?environment= &status= &limit=
app.get('/deployments', async (c) => {
  try {
    const environment = c.req.query('environment');
    const status = c.req.query('status');
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const deployments = await adminDeploymentManagerService.listDeployments(c.env.DB, { environment, status, limit });
    return c.json({ deployments, count: deployments.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /deployments — create deployment
app.post('/deployments', async (c) => {
  try {
    const body = await c.req.json<{
      version: string;
      environment?: string;
      deploy_type?: string;
      commit_hash?: string;
      release_notes?: string;
      deployed_by?: string;
      health_check_url?: string;
    }>();
    if (!body.version) return c.json({ error: 'version is required' }, 400);
    const deployment = await adminDeploymentManagerService.createDeployment(c.env.DB, body);
    return c.json(deployment, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — admin overview summary
app.get('/dashboard', async (c) => {
  try {
    const overview = await adminDeploymentManagerService.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /deployments/:id — get deployment detail
app.get('/deployments/:id', async (c) => {
  try {
    const deployment = await adminDeploymentManagerService.getDeployment(c.env.DB, c.req.param('id'));
    if (!deployment) return c.json({ error: 'Deployment not found' }, 404);
    return c.json(deployment);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /deployments/:id/start — mark deployment as running
app.post('/deployments/:id/start', async (c) => {
  try {
    const deployment = await adminDeploymentManagerService.startDeployment(c.env.DB, c.req.param('id'));
    if (!deployment) return c.json({ error: 'Deployment not found' }, 404);
    return c.json(deployment);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /deployments/:id/complete — complete deployment with status
app.post('/deployments/:id/complete', async (c) => {
  try {
    const body = await c.req.json<{ status: string }>();
    if (!body.status) return c.json({ error: 'status is required' }, 400);
    const deployment = await adminDeploymentManagerService.completeDeployment(c.env.DB, c.req.param('id'), body.status);
    if (!deployment) return c.json({ error: 'Deployment not found' }, 404);
    return c.json(deployment);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /deployments/:id/rollback — initiate rollback
app.post('/deployments/:id/rollback', async (c) => {
  try {
    const rollback = await adminDeploymentManagerService.rollback(c.env.DB, c.req.param('id'));
    if (!rollback) return c.json({ error: 'Deployment not found' }, 404);
    return c.json(rollback, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /deployments/:id/checks — get all checks for a deployment
app.get('/deployments/:id/checks', async (c) => {
  try {
    const checks = await adminDeploymentManagerService.getChecks(c.env.DB, c.req.param('id'));
    return c.json({ checks, count: checks.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /deployments/:id/checks — add check result
app.post('/deployments/:id/checks', async (c) => {
  try {
    const body = await c.req.json<{ check_type: string; result_json?: Record<string, unknown> }>();
    if (!body.check_type) return c.json({ error: 'check_type is required' }, 400);
    const check = await adminDeploymentManagerService.addCheck(c.env.DB, c.req.param('id'), body.check_type, body.result_json);
    return c.json(check, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /deployments/:id/canary — get canary config
app.get('/deployments/:id/canary', async (c) => {
  try {
    const config = await adminDeploymentManagerService.getCanaryConfig(c.env.DB, c.req.param('id'));
    if (!config) return c.json({ error: 'Canary config not found' }, 404);
    return c.json(config);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /deployments/:id/canary — set canary config
app.put('/deployments/:id/canary', async (c) => {
  try {
    const body = await c.req.json<{
      percentage?: number;
      duration_minutes?: number;
      success_threshold?: number;
      auto_promote?: number;
      metrics_json?: Record<string, unknown>;
    }>();
    const config = await adminDeploymentManagerService.setCanaryConfig(c.env.DB, c.req.param('id'), body);
    return c.json(config);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /deployments/:id/canary/promote — promote canary to full
app.post('/deployments/:id/canary/promote', async (c) => {
  try {
    const deployment = await adminDeploymentManagerService.promoteCanary(c.env.DB, c.req.param('id'));
    if (!deployment) return c.json({ error: 'Deployment not found' }, 404);
    return c.json(deployment);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminDeploymentManager };
