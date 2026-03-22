/**
 * Mission Collaboration routes — collaborators roster and threaded comments
 *
 * Authenticated routes (tenant-scoped):
 *   GET  /missions/:missionId/collaborators  — list collaborators for a mission
 *   POST /missions/:missionId/collaborators  — add a collaborator to a mission
 *   GET  /missions/:missionId/comments       — get comments for a mission
 *
 * Admin route (X-Admin-Key protected):
 *   GET  /admin/overview                     — aggregated overview across all tenants
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionCollaborationService } from '../services/mission-collaboration';

// Inline Bindings — no Env import from index
type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
  [key: string]: unknown;
};

const app = new Hono<{ Bindings: Bindings }>();

// ─── Authenticated routes ─────────────────────────────────────────────────────

/**
 * GET /missions/:missionId/collaborators
 * List all collaborators for a mission (tenant-scoped).
 */
app.get('/missions/:missionId/collaborators', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('missionId');

  try {
    const result = await missionCollaborationService.listCollaborators(
      c.env.DB,
      tenant.tenantId,
      missionId
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /missions/:missionId/collaborators
 * Add a collaborator to a mission.
 * Body: { user_id, role?, invited_by? }
 */
app.post('/missions/:missionId/collaborators', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('missionId');
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

  const userId = typeof body.user_id === 'string' ? body.user_id.trim() : '';
  if (!userId) {
    return c.json({ error: 'user_id is required' }, 400);
  }

  const role = typeof body.role === 'string' ? body.role.trim() : 'viewer';
  const invitedBy = typeof body.invited_by === 'string' ? body.invited_by.trim() : undefined;

  try {
    const result = await missionCollaborationService.addCollaborator(
      c.env.DB,
      tenant.tenantId,
      missionId,
      userId,
      role,
      invitedBy
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /missions/:missionId/comments
 * Get comments for a mission (tenant-scoped).
 * Query param: parent_id (optional — filter by thread root)
 */
app.get('/missions/:missionId/comments', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.param('missionId');
  const parentIdParam = c.req.query('parent_id');

  // undefined = no filter, 'null' string = top-level only, otherwise filter by id
  let parentId: string | null | undefined;
  if (parentIdParam === undefined) {
    parentId = undefined;
  } else if (parentIdParam === 'null' || parentIdParam === '') {
    parentId = null;
  } else {
    parentId = parentIdParam;
  }

  try {
    const result = await missionCollaborationService.getComments(
      c.env.DB,
      tenant.tenantId,
      missionId,
      parentId
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ─── Admin route ─────────────────────────────────────────────────────────────

/**
 * GET /admin/overview
 * Aggregated collaborator and comment stats across all tenants.
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var.
 */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!key || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await missionCollaborationService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as missionCollaboration };
