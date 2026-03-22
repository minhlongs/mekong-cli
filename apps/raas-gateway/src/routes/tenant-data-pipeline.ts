/**
 * Tenant Data Pipeline routes — manage ETL pipelines and view run history
 * Auth:  GET /pipelines, POST /pipelines, GET /runs
 * Admin: GET /admin/overview (X-Admin-Key)
 */
import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantDataPipelineService } from '../services/tenant-data-pipeline-service';

const app = new Hono<{ Bindings: Env }>();

function isAdmin(c: any): boolean {
  return !!(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

/** GET /pipelines — list pipelines for authenticated tenant */
app.get('/pipelines', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const status = c.req.query('status');
    const records = await tenantDataPipelineService.listPipelines(c.env.DB, tenant.tenantId, { status });
    return c.json({ success: true, data: records });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to list pipelines' }, 500);
  }
});

/** POST /pipelines — create a new pipeline for authenticated tenant */
app.post('/pipelines', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{
      pipeline_name: string;
      source_type: string;
      destination_type: string;
      transform_config_json?: string;
      schedule_cron?: string;
    }>();
    if (!body.pipeline_name) return c.json({ error: 'pipeline_name is required' }, 400);
    if (!body.source_type) return c.json({ error: 'source_type is required' }, 400);
    if (!body.destination_type) return c.json({ error: 'destination_type is required' }, 400);

    const record = await tenantDataPipelineService.createPipeline(c.env.DB, tenant.tenantId, body);
    return c.json({ success: true, data: record }, 201);
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to create pipeline' }, 500);
  }
});

/** GET /runs — list pipeline runs for authenticated tenant */
app.get('/runs', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const pipeline_id = c.req.query('pipeline_id');
    const limit = c.req.query('limit') ? Number(c.req.query('limit')) : undefined;
    const records = await tenantDataPipelineService.getRuns(c.env.DB, tenant.tenantId, { pipeline_id, limit });
    return c.json({ success: true, data: records });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to list runs' }, 500);
  }
});

/** GET /admin/overview — platform-wide pipeline stats (admin only) */
app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Forbidden' }, 403);
  try {
    const overview = await tenantDataPipelineService.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantDataPipeline };
