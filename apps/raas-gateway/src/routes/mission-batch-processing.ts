/**
 * Mission Batch Processing routes — create and track mission batches
 *
 * Tenant (auth): GET /batches, POST /batches, GET /items
 * Admin (X-Admin-Key): GET /admin/overview
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionBatchProcessingService } from '../services/mission-batch-processing';

type Bindings = {
  DB: any;
  ADMIN_API_KEY?: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// ── Tenant routes (auth required) ────────────────────────────────────────────

/**
 * GET /batches — list all batch jobs for the authenticated tenant
 */
app.get('/batches', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const result = await missionBatchProcessingService.listBatches(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 400);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
});

/**
 * POST /batches — create a new batch job
 * Body: { batch_name: string, missions: Array<{ mission_id? }> }
 */
app.post('/batches', auth(), async (c) => {
  const tenant = getTenant(c);

  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400);
  }

  const batchName = (body.batch_name as string)?.trim();
  if (!batchName) return c.json({ error: 'batch_name is required' }, 400);

  const missions = Array.isArray(body.missions) ? (body.missions as Array<{ mission_id?: string }>) : [];

  try {
    const result = await missionBatchProcessingService.createBatch(
      c.env.DB,
      tenant.tenantId,
      batchName,
      missions
    );
    if (!result.success) return c.json({ error: result.error }, 400);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
});

/**
 * GET /items — get items for a specific batch
 * Query: ?batch_id=<id>
 */
app.get('/items', auth(), async (c) => {
  const tenant = getTenant(c);
  const batchId = c.req.query('batch_id')?.trim();

  if (!batchId) return c.json({ error: 'batch_id query param is required' }, 400);

  try {
    const result = await missionBatchProcessingService.getItems(c.env.DB, tenant.tenantId, batchId);
    if (!result.success) return c.json({ error: result.error }, 404);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
});

// ── Admin routes (X-Admin-Key required) ──────────────────────────────────────

/**
 * GET /admin/overview — aggregate stats across all tenants
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await missionBatchProcessingService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: err instanceof Error ? err.message : 'Internal error' }, 500);
  }
});

export { app as missionBatchProcessing };
