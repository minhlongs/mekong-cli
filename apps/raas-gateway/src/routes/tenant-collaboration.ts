/**
 * Tenant Collaboration routes — comments, shared views, activity feed
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  addComment,
  listComments,
  deleteComment,
  createSharedView,
  listSharedViews,
  deleteSharedView,
  getActivityFeed,
  logActivity,
  getCollaborationStats,
  getAdminCollaborationOverview,
} from '../services/tenant-collaboration-service';

export const tenantCollaboration = new Hono<{ Bindings: Env }>();

// ── Admin auth helper ──────────────────────────────────────────────────────────

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Comments ───────────────────────────────────────────────────────────────────

/**
 * GET /comments/:missionId — List all comments for a mission
 */
tenantCollaboration.get('/comments/:missionId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const missionId = c.req.param('missionId');
  try {
    const comments = await listComments(c.env.DB, tenantId, missionId);
    return json({ comments });
  } catch (err) {
    return json({ error: 'Failed to list comments', details: String(err) }, { status: 500 });
  }
});

/**
 * POST /comments/:missionId — Add a comment (supports threaded replies via parent_id)
 */
tenantCollaboration.post('/comments/:missionId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const missionId = c.req.param('missionId');
  const body = await c.req.json().catch(() => ({})) as { content?: string; parent_id?: string };

  if (!body.content?.trim()) {
    return json({ error: 'content is required' }, { status: 400 });
  }

  try {
    const comment = await addComment(c.env.DB, tenantId, missionId, tenantId, body.content.trim(), body.parent_id);
    await logActivity(c.env.DB, tenantId, tenantId, 'comment_added', 'mission', missionId, { comment_id: comment.id });
    return json({ comment }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to add comment', details: String(err) }, { status: 500 });
  }
});

/**
 * DELETE /comments/:commentId — Delete own comment
 */
tenantCollaboration.delete('/comments/:commentId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const commentId = c.req.param('commentId');
  try {
    const result = await deleteComment(c.env.DB, tenantId, commentId, tenantId);
    if (!result.deleted) {
      return json({ error: 'Comment not found or not owned by you' }, { status: 404 });
    }
    return json({ deleted: true });
  } catch (err) {
    return json({ error: 'Failed to delete comment', details: String(err) }, { status: 500 });
  }
});

// ── Shared Views ───────────────────────────────────────────────────────────────

/**
 * GET /views — List shared views accessible to authenticated user
 */
tenantCollaboration.get('/views', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const views = await listSharedViews(c.env.DB, tenantId, tenantId);
    return json({ views });
  } catch (err) {
    return json({ error: 'Failed to list views', details: String(err) }, { status: 500 });
  }
});

/**
 * POST /views — Create a shared view
 * Body: { name, view_type, filters?, shared_with? }
 */
tenantCollaboration.post('/views', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    name?: string;
    view_type?: string;
    filters?: unknown;
    shared_with?: string[] | 'all';
  };

  if (!body.name?.trim()) {
    return json({ error: 'name is required' }, { status: 400 });
  }

  const viewType = body.view_type ?? 'mission_list';
  const validTypes = ['mission_list', 'dashboard', 'analytics'];
  if (!validTypes.includes(viewType)) {
    return json({ error: `view_type must be one of: ${validTypes.join(', ')}` }, { status: 400 });
  }

  try {
    const view = await createSharedView(
      c.env.DB, tenantId, tenantId, body.name.trim(), viewType, body.filters, body.shared_with
    );
    await logActivity(c.env.DB, tenantId, tenantId, 'view_shared', 'view', view.id, { name: view.name });
    return json({ view }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to create view', details: String(err) }, { status: 500 });
  }
});

/**
 * DELETE /views/:viewId — Delete own shared view
 */
tenantCollaboration.delete('/views/:viewId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const viewId = c.req.param('viewId');
  try {
    const result = await deleteSharedView(c.env.DB, tenantId, viewId, tenantId);
    if (!result.deleted) {
      return json({ error: 'View not found or not owned by you' }, { status: 404 });
    }
    return json({ deleted: true });
  } catch (err) {
    return json({ error: 'Failed to delete view', details: String(err) }, { status: 500 });
  }
});

// ── Activity Feed ──────────────────────────────────────────────────────────────

/**
 * GET /feed — Paginated activity feed for tenant
 * Query: limit (default 50), offset (default 0)
 */
tenantCollaboration.get('/feed', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 100);
  const offset = parseInt(c.req.query('offset') ?? '0', 10) || 0;
  try {
    const feed = await getActivityFeed(c.env.DB, tenantId, limit, offset);
    return json({ feed, limit, offset });
  } catch (err) {
    return json({ error: 'Failed to get activity feed', details: String(err) }, { status: 500 });
  }
});

// ── Stats ──────────────────────────────────────────────────────────────────────

/**
 * GET /stats — Collaboration counts for authenticated tenant
 */
tenantCollaboration.get('/stats', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const stats = await getCollaborationStats(c.env.DB, tenantId);
    return json({ stats });
  } catch (err) {
    return json({ error: 'Failed to get stats', details: String(err) }, { status: 500 });
  }
});

// ── Admin ──────────────────────────────────────────────────────────────────────

/**
 * GET /admin/overview — Most active tenants by collaboration (admin only)
 */
tenantCollaboration.get('/admin/overview', async (c) => {
  if (!requireAdminKey(c)) {
    return json({ error: 'Forbidden' }, { status: 403 });
  }
  try {
    const overview = await getAdminCollaborationOverview(c.env.DB);
    return json({ overview });
  } catch (err) {
    return json({ error: 'Failed to get admin overview', details: String(err) }, { status: 500 });
  }
});
