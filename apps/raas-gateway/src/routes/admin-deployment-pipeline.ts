/**
 * Admin Deployment Pipeline Routes — pipeline CRUD and run history
 * All endpoints require X-Admin-Key header (403 on failure)
 */

import { Hono } from 'hono';
import * as svc from '../services/admin-deployment-pipeline';

interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
}

const app = new Hono<{ Bindings: Bindings }>();

// Admin-only guard — 403 on missing or invalid key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /admin/deployment-pipelines — list all pipelines, optional ?environment filter
app.get('/pipelines', async (c) => {
  try {
    const environment = c.req.query('environment');
    const result = await svc.listPipelines(c.env.DB, environment);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e) {
    return c.json({ error: String(e) }, 500);
  }
});

// POST /admin/deployment-pipelines — create a new pipeline
app.post('/pipelines', async (c) => {
  try {
    const body = await c.req.json<{ pipeline_name?: string; environment?: string; stages_json?: string }>();
    if (!body.pipeline_name) return c.json({ error: 'pipeline_name required' }, 400);
    if (!body.stages_json) return c.json({ error: 'stages_json required' }, 400);
    const result = await svc.createPipeline(c.env.DB, {
      pipeline_name: body.pipeline_name,
      environment: body.environment,
      stages_json: body.stages_json,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (e) {
    return c.json({ error: String(e) }, 500);
  }
});

// GET /admin/deployment-pipelines/runs — run history, optional ?pipeline_id filter
app.get('/runs', async (c) => {
  try {
    const pipelineId = c.req.query('pipeline_id');
    const result = await svc.getRuns(c.env.DB, pipelineId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e) {
    return c.json({ error: String(e) }, 500);
  }
});

// GET /admin/deployment-pipelines/dashboard — summary stats
app.get('/dashboard', async (c) => {
  try {
    const result = await svc.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (e) {
    return c.json({ error: String(e) }, 500);
  }
});

export { app as adminDeploymentPipeline };
