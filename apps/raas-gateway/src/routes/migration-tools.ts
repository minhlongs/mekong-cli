/**
 * Migration tools routes — data import/export for competitor platform onboarding
 * Supports bulk tenant migration from zapier, make, n8n, custom platforms
 */
import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createMigrationJob,
  getMigrationJob,
  listMigrationJobs,
  processImport,
  generateExport,
  getMappings,
  getAdminMigrationStats,
  SUPPORTED_PLATFORMS,
  SUPPORTED_DATA_TYPES,
} from '../services/migration-tools-service';

const app = new Hono<{ Bindings: Env }>();

/** GET /supported-platforms — public, no auth */
app.get('/supported-platforms', (c) => {
  return c.json({
    success: true,
    data: {
      platforms: SUPPORTED_PLATFORMS,
      data_types: SUPPORTED_DATA_TYPES,
    },
  });
});

/** POST /jobs — create migration job */
app.post('/jobs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json().catch(() => ({}));
    const { direction, source_platform, data_types } = body as {
      direction?: string;
      source_platform?: string;
      data_types?: string[];
    };

    if (!direction || !['import', 'export'].includes(direction)) {
      return c.json({ error: 'direction must be "import" or "export"' }, 400);
    }
    if (!Array.isArray(data_types) || data_types.length === 0) {
      return c.json({ error: 'data_types must be a non-empty array' }, 400);
    }

    const job = await createMigrationJob(
      c.env.DB,
      tenantId,
      direction,
      source_platform ?? null,
      data_types
    );
    return c.json({ success: true, data: job }, 201);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /jobs — list all migration jobs for tenant */
app.get('/jobs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const jobs = await listMigrationJobs(c.env.DB, tenantId);
    return c.json({ success: true, data: jobs });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /jobs/:jobId — get single job status */
app.get('/jobs/:jobId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const jobId = c.req.param('jobId');
  try {
    const job = await getMigrationJob(c.env.DB, tenantId, jobId);
    if (!job) return c.json({ error: 'Job not found' }, 404);
    return c.json({ success: true, data: job });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** POST /import/:jobId — upload import payload and process */
app.post('/import/:jobId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const jobId = c.req.param('jobId');
  try {
    const body = await c.req.json().catch(() => ({}));
    const { data } = body as { data?: Record<string, unknown[]> };

    if (!data || typeof data !== 'object') {
      return c.json({ error: 'data object is required' }, 400);
    }

    const job = await getMigrationJob(c.env.DB, tenantId, jobId);
    if (!job) return c.json({ error: 'Job not found' }, 404);
    if (job.status === 'processing') {
      return c.json({ error: 'Job is already processing' }, 409);
    }

    // Process async — respond immediately then process
    await processImport(c.env.DB, tenantId, jobId, data);
    const updated = await getMigrationJob(c.env.DB, tenantId, jobId);
    return c.json({ success: true, data: updated });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /export — export tenant data as JSON */
app.get('/export', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const typesParam = c.req.query('types') ?? '';
    const dataTypes = typesParam
      ? typesParam.split(',').map((t) => t.trim()).filter(Boolean)
      : SUPPORTED_DATA_TYPES;

    const data = await generateExport(c.env.DB, tenantId, dataTypes);
    return c.json({ success: true, data, exported_at: new Date().toISOString() });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /jobs/:jobId/mappings — get source→target ID mappings */
app.get('/jobs/:jobId/mappings', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const jobId = c.req.param('jobId');
  try {
    const job = await getMigrationJob(c.env.DB, tenantId, jobId);
    if (!job) return c.json({ error: 'Job not found' }, 404);

    const mappings = await getMappings(c.env.DB, jobId);
    return c.json({ success: true, data: mappings });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /admin/stats — platform-wide migration statistics (admin only) */
app.get('/admin/stats', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const stats = await getAdminMigrationStats(c.env.DB);
    return c.json({ success: true, data: stats });
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

export { app as migrationTools };
