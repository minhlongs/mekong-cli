/**
 * Mission Output Artifacts routes — manage files/outputs produced by missions
 *
 * Authenticated routes (tenant-scoped):
 *   GET  /artifacts          — list artifacts (query: mission_id)
 *   POST /artifacts          — create artifact record
 *   GET  /downloads/:id      — record download + get download history
 *
 * Admin route (X-Admin-Key required):
 *   GET  /admin/overview     — aggregate stats across all tenants
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionOutputArtifactsService } from '../services/mission-output-artifacts';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
  RATE_LIMIT_KV: any;
  SESSION_KV: any;
  AI: any;
  JWT_SECRET=REDACTED: string;
  POLAR_WEBHOOK_SECRET: string;
  TELEGRAM_BOT_TOKEN: string;
  ENVIRONMENT: string;
  LOG_LEVEL: string;
};

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /artifacts
 * List all artifacts for the authenticated tenant.
 * Query param: mission_id (optional filter)
 */
app.get('/artifacts', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.query('mission_id');

  try {
    const result = await missionOutputArtifactsService.listArtifacts(
      c.env.DB,
      tenant.tenantId,
      missionId
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list artifacts' }, 500);
  }
});

/**
 * POST /artifacts
 * Create a new artifact record for a mission.
 * Body: { mission_id, artifact_name, artifact_type?, file_url?, file_size?, content_type? }
 */
app.post('/artifacts', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, any>;

  const mission_id = typeof body.mission_id === 'string' ? body.mission_id.trim() : '';
  const artifact_name = typeof body.artifact_name === 'string' ? body.artifact_name.trim() : '';

  if (!mission_id || !artifact_name) {
    return c.json({ error: 'mission_id and artifact_name are required' }, 400);
  }

  try {
    const result = await missionOutputArtifactsService.createArtifact(c.env.DB, {
      id: crypto.randomUUID(),
      tenant_id: tenant.tenantId,
      mission_id,
      artifact_name,
      artifact_type: typeof body.artifact_type === 'string' ? body.artifact_type : 'file',
      file_url: typeof body.file_url === 'string' ? body.file_url : undefined,
      file_size: typeof body.file_size === 'number' ? body.file_size : undefined,
      content_type: typeof body.content_type === 'string' ? body.content_type : undefined,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Failed to create artifact' }, 500);
  }
});

/**
 * GET /downloads/:id
 * Record a download event for artifact :id and return full download history.
 * Query param: downloaded_by (optional identifier)
 */
app.get('/downloads/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const artifactId = c.req.param('id');
  const downloadedBy = c.req.query('downloaded_by');

  try {
    const result = await missionOutputArtifactsService.getDownloads(
      c.env.DB,
      tenant.tenantId,
      artifactId,
      downloadedBy
    );
    if (!result.success) {
      const status = result.error === 'Artifact not found' ? 404 : 500;
      return c.json({ error: result.error }, status);
    }
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to record download' }, 500);
  }
});

/**
 * GET /admin/overview
 * Aggregate artifact and download stats across all tenants.
 * Requires X-Admin-Key header.
 */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await missionOutputArtifactsService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as missionOutputArtifacts };
