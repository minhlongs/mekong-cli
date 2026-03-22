/**
 * Mission Result Storage routes — store and retrieve versioned mission results + attachments
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { missionResultStorageService as svc } from '../services/mission-result-storage-service';

const app = new Hono<{ Bindings: Env }>();

// Admin auth via X-Admin-Key header
const adminAuth = () => async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  }
  await next();
};

/**
 * POST /results — Store a new versioned result for a mission
 * Body: { mission_id, result_type?, content?, metadata_json? }
 */
app.post('/results', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch { return json({ error: 'Invalid JSON' }, { status: 400 }); }

  const missionId = (body.mission_id as string)?.trim();
  if (!missionId) return json({ error: 'mission_id is required', code: 'MISSING_MISSION_ID' }, { status: 400 });

  try {
    const result = await svc.storeResult(c.env.DB, tenant.tenantId, missionId, {
      result_type: body.result_type as string | undefined,
      content: body.content as string | undefined,
      metadata_json: body.metadata_json as string | undefined,
    });
    return json({ result }, { status: 201 });
  } catch (err: any) {
    // UNIQUE constraint on (mission_id, version) — concurrent write collision
    if (err?.message?.includes('UNIQUE')) return json({ error: 'Version conflict, retry', code: 'VERSION_CONFLICT' }, { status: 409 });
    return json({ error: 'Failed to store result' }, { status: 500 });
  }
});

/**
 * GET /results/:missionId — Get latest result for a mission
 */
app.get('/results/:missionId', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const result = await svc.getResult(c.env.DB, tenant.tenantId, c.req.param('missionId'));
    if (!result) return json({ error: 'Result not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ result });
  } catch { return json({ error: 'Failed to fetch result' }, { status: 500 }); }
});

/**
 * GET /results/:missionId/versions — List all versions of a mission result
 */
app.get('/results/:missionId/versions', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const versions = await svc.getResultVersions(c.env.DB, tenant.tenantId, c.req.param('missionId'));
    return json({ versions, total: versions.length });
  } catch { return json({ error: 'Failed to fetch versions' }, { status: 500 }); }
});

/**
 * GET /results/:missionId/versions/:version — Get a specific version
 */
app.get('/results/:missionId/versions/:version', auth(), async (c) => {
  const tenant = getTenant(c);
  const version = parseInt(c.req.param('version'));
  if (isNaN(version) || version < 1) return json({ error: 'Invalid version number', code: 'INVALID_VERSION' }, { status: 400 });
  try {
    const result = await svc.getResultByVersion(c.env.DB, tenant.tenantId, c.req.param('missionId'), version);
    if (!result) return json({ error: 'Version not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ result });
  } catch { return json({ error: 'Failed to fetch version' }, { status: 500 }); }
});

/**
 * POST /results/:resultId/attachments — Add attachment metadata to a result
 * Body: { filename, content_type?, size_bytes?, storage_url?, checksum? }
 */
app.post('/results/:resultId/attachments', auth(), async (c) => {
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch { return json({ error: 'Invalid JSON' }, { status: 400 }); }

  const filename = (body.filename as string)?.trim();
  if (!filename) return json({ error: 'filename is required', code: 'MISSING_FILENAME' }, { status: 400 });

  try {
    const attachment = await svc.addAttachment(c.env.DB, c.req.param('resultId'), {
      filename,
      content_type: body.content_type as string | undefined,
      size_bytes: body.size_bytes as number | undefined,
      storage_url: body.storage_url as string | undefined,
      checksum: body.checksum as string | undefined,
    });
    return json({ attachment }, { status: 201 });
  } catch { return json({ error: 'Failed to add attachment' }, { status: 500 }); }
});

/**
 * GET /results/:resultId/attachments — List attachments for a result
 */
app.get('/results/:resultId/attachments', auth(), async (c) => {
  try {
    const attachments = await svc.listAttachments(c.env.DB, c.req.param('resultId'));
    return json({ attachments, total: attachments.length });
  } catch { return json({ error: 'Failed to list attachments' }, { status: 500 }); }
});

/**
 * DELETE /attachments/:id — Delete an attachment by id
 */
app.delete('/attachments/:id', auth(), async (c) => {
  try {
    const deleted = await svc.deleteAttachment(c.env.DB, c.req.param('id'));
    if (!deleted) return json({ error: 'Attachment not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ success: true });
  } catch { return json({ error: 'Failed to delete attachment' }, { status: 500 }); }
});

/**
 * GET /stats — Storage stats for authenticated tenant
 */
app.get('/stats', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const stats = await svc.getStorageStats(c.env.DB, tenant.tenantId);
    return json({ stats });
  } catch { return json({ error: 'Failed to fetch stats' }, { status: 500 }); }
});

/**
 * GET /admin/overview — Admin overview across all tenants (X-Admin-Key required)
 */
app.get('/admin/overview', adminAuth(), async (c) => {
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return json({ overview });
  } catch { return json({ error: 'Failed to fetch admin overview' }, { status: 500 }); }
});

export { app as missionResultStorage };
