/**
 * Mission Artifact Storage routes — list/create artifacts + download audit + admin overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { missionArtifactStorageService as svc } from '../services/mission-artifact-storage-service';

const app = new Hono<{ Bindings: Env }>();

/**
 * GET /artifacts — List artifacts for authenticated tenant, optional ?mission_id filter
 */
app.get('/artifacts', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.query('mission_id');
  try {
    const artifacts = await svc.listArtifacts(c.env.DB, tenant.tenantId, missionId);
    return json({ artifacts, total: artifacts.length });
  } catch { return json({ error: 'Failed to list artifacts' }, { status: 500 }); }
});

/**
 * POST /artifacts — Create a new artifact record
 * Body: { mission_id, file_name, storage_path, content_type, artifact_type?, file_size? }
 */
app.post('/artifacts', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch { return json({ error: 'Invalid JSON' }, { status: 400 }); }

  const missionId = (body.mission_id as string)?.trim();
  const fileName = (body.file_name as string)?.trim();
  const storagePath = (body.storage_path as string)?.trim();
  const contentType = (body.content_type as string)?.trim();

  if (!missionId) return json({ error: 'mission_id is required', code: 'MISSING_MISSION_ID' }, { status: 400 });
  if (!fileName) return json({ error: 'file_name is required', code: 'MISSING_FILE_NAME' }, { status: 400 });
  if (!storagePath) return json({ error: 'storage_path is required', code: 'MISSING_STORAGE_PATH' }, { status: 400 });
  if (!contentType) return json({ error: 'content_type is required', code: 'MISSING_CONTENT_TYPE' }, { status: 400 });

  try {
    const artifact = await svc.createArtifact(c.env.DB, tenant.tenantId, {
      mission_id: missionId,
      file_name: fileName,
      storage_path: storagePath,
      content_type: contentType,
      artifact_type: body.artifact_type as string | undefined,
      file_size: body.file_size as number | undefined,
    });
    return json({ artifact }, { status: 201 });
  } catch { return json({ error: 'Failed to create artifact' }, { status: 500 }); }
});

/**
 * GET /downloads — List download events for a specific artifact (?artifact_id required)
 */
app.get('/downloads', auth(), async (c) => {
  const tenant = getTenant(c);
  const artifactId = c.req.query('artifact_id');
  if (!artifactId) return json({ error: 'artifact_id query param required', code: 'MISSING_ARTIFACT_ID' }, { status: 400 });
  try {
    const downloads = await svc.getDownloads(c.env.DB, tenant.tenantId, artifactId);
    return json({ downloads, total: downloads.length });
  } catch { return json({ error: 'Failed to fetch downloads' }, { status: 500 }); }
});

/**
 * GET /admin/overview — Platform-wide artifact stats (X-Admin-Key required)
 */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  }
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return json({ overview });
  } catch { return json({ error: 'Failed to fetch admin overview' }, { status: 500 }); }
});

export { app as missionArtifactStorage };
