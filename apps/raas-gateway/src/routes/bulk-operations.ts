/**
 * Bulk operations routes — batch import/export for missions, api_keys, team_members, webhooks
 * POST /bulk/export   — create export job
 * POST /bulk/import   — create import job
 * GET  /bulk/jobs     — list jobs
 * GET  /bulk/jobs/:id — get job status
 * POST /bulk/jobs/:id/cancel — cancel job
 * GET  /bulk/stats    — aggregate stats
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createBulkExport,
  createBulkImport,
  getBulkJob,
  listBulkJobs,
  cancelBulkJob,
  getBulkStats,
  type BulkJob,
} from '../services/bulk-operations-service';

export const bulkOperations = new Hono<{ Bindings: Env }>();

const VALID_RESOURCES: BulkJob['resource'][] = ['missions', 'api_keys', 'team_members', 'webhooks'];
const VALID_FORMATS = ['json', 'csv'] as const;

/** POST /bulk/export */
bulkOperations.post('/export', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    resource?: string;
    format?: string;
    filters?: Record<string, string>;
  };

  const resource = body.resource as BulkJob['resource'];
  if (!resource || !VALID_RESOURCES.includes(resource)) {
    return json({ error: `resource must be one of: ${VALID_RESOURCES.join(', ')}`, code: 'INVALID_RESOURCE' }, { status: 400 });
  }

  const format = (VALID_FORMATS as readonly string[]).includes(body.format ?? '') ? body.format as 'json' | 'csv' : 'json';

  try {
    const job = await createBulkExport(c.env.DB, tenant.tenantId, resource, { format, filters: body.filters });

    // For CSV exports return file directly; for JSON return inline when job completed
    if (format === 'csv' && job.status === 'completed') {
      const raw = await c.env.DB.prepare('SELECT result_data FROM bulk_jobs WHERE id = ?').bind(job.id).first<{ result_data: string }>();
      return new Response(raw?.result_data ?? '', {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename="export-${resource}-${job.id}.csv"`,
        },
      });
    }

    return json({ success: true, data: job }, { status: 201 });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'Export failed', code: 'EXPORT_ERROR' }, { status: 500 });
  }
});

/** POST /bulk/import */
bulkOperations.post('/import', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    resource?: string;
    items?: unknown[];
  };

  const resource = body.resource as BulkJob['resource'];
  if (!resource || !VALID_RESOURCES.includes(resource)) {
    return json({ error: `resource must be one of: ${VALID_RESOURCES.join(', ')}`, code: 'INVALID_RESOURCE' }, { status: 400 });
  }

  const items = body.items;
  if (!Array.isArray(items) || items.length === 0) {
    return json({ error: 'items array is required and must not be empty', code: 'INVALID_ITEMS' }, { status: 400 });
  }
  if (items.length > 500) {
    return json({ error: 'Max 500 items per import batch', code: 'BATCH_TOO_LARGE' }, { status: 400 });
  }

  try {
    const job = await createBulkImport(c.env.DB, tenant.tenantId, resource, items as Record<string, unknown>[]);
    return json({ success: true, data: job }, { status: 201 });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'Import failed', code: 'IMPORT_ERROR' }, { status: 500 });
  }
});

/** GET /bulk/jobs */
bulkOperations.get('/jobs', auth(), async (c) => {
  const tenant = getTenant(c);
  const type = c.req.query('type');
  const resource = c.req.query('resource');
  const limit = parseInt(c.req.query('limit') ?? '20', 10);

  const jobs = await listBulkJobs(c.env.DB, tenant.tenantId, { type, resource, limit });
  return json({ success: true, data: jobs, count: jobs.length });
});

/** GET /bulk/jobs/:id */
bulkOperations.get('/jobs/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const jobId = c.req.param('id');

  const job = await getBulkJob(c.env.DB, tenant.tenantId, jobId);
  if (!job) return json({ error: 'Job not found', code: 'NOT_FOUND' }, { status: 404 });

  return json({ success: true, data: job });
});

/** POST /bulk/jobs/:id/cancel */
bulkOperations.post('/jobs/:id/cancel', auth(), async (c) => {
  const tenant = getTenant(c);
  const jobId = c.req.param('id');

  const result = await cancelBulkJob(c.env.DB, tenant.tenantId, jobId);
  if (!result.success) {
    return json({ error: result.error, code: 'CANCEL_FAILED' }, { status: 400 });
  }
  return json({ success: true });
});

/** GET /bulk/stats */
bulkOperations.get('/stats', auth(), async (c) => {
  const tenant = getTenant(c);
  const stats = await getBulkStats(c.env.DB, tenant.tenantId);
  return json({ success: true, data: stats });
});
