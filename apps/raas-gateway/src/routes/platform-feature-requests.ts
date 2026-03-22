/**
 * Platform Feature Requests routes — tenant roadmap requests with voting and comments
 * Public:  GET /requests, GET /requests/:id, GET /requests/:id/comments
 * Auth:    POST /requests, POST|DELETE /requests/:id/vote, POST /requests/:id/comments
 * Admin:   PUT /admin/requests/:id, GET /admin/overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createRequest, listRequests, getRequest, updateRequest,
  voteForRequest, removeVote, addComment, listComments,
  updateRequestStatus, getAdminFeatureOverview,
} from '../services/platform-feature-requests-service';
import type { FeatureCategory, FeatureStatus, FeaturePriority } from '../services/platform-feature-requests-service';

const app = new Hono<{ Bindings: Env }>();

const CATEGORIES: FeatureCategory[] = ['general', 'api', 'dashboard', 'billing', 'integrations', 'security'];
const STATUSES: FeatureStatus[] = ['submitted', 'under_review', 'planned', 'in_progress', 'completed', 'declined'];
const PRIORITIES: FeaturePriority[] = ['low', 'medium', 'high', 'critical'];

const requireAdminKey = async (c: any, next: any) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY)
    return c.json({ error: 'Unauthorized' }, 401);
  await next();
};

// ── Public ─────────────────────────────────────────────────────────────────────

app.get('/requests', async (c) => {
  try {
    const sort = c.req.query('sort') === 'date' ? 'date' : 'votes';
    const status = c.req.query('status');
    const category = c.req.query('category');
    const limit = Math.min(parseInt(c.req.query('limit') ?? '20', 10), 100);
    const offset = parseInt(c.req.query('offset') ?? '0', 10);

    if (status && !STATUSES.includes(status as FeatureStatus))
      return c.json({ error: `status must be one of: ${STATUSES.join(', ')}` }, 400);
    if (category && !CATEGORIES.includes(category as FeatureCategory))
      return c.json({ error: `category must be one of: ${CATEGORIES.join(', ')}` }, 400);

    const requests = await listRequests(c.env.DB, { sort, status, category, limit, offset });
    return c.json({ ok: true, count: requests.length, data: requests });
  } catch (err) {
    return c.json({ error: 'Failed to list feature requests', details: String(err) }, 500);
  }
});

app.get('/requests/:requestId', async (c) => {
  try {
    const request = await getRequest(c.env.DB, c.req.param('requestId'));
    if (!request) return c.json({ error: 'Feature request not found' }, 404);
    return c.json({ ok: true, data: request });
  } catch (err) {
    return c.json({ error: 'Failed to fetch feature request', details: String(err) }, 500);
  }
});

app.get('/requests/:requestId/comments', async (c) => {
  try {
    const requestId = c.req.param('requestId');
    if (!await getRequest(c.env.DB, requestId)) return c.json({ error: 'Feature request not found' }, 404);
    const comments = await listComments(c.env.DB, requestId);
    return c.json({ ok: true, count: comments.length, data: comments });
  } catch (err) {
    return c.json({ error: 'Failed to list comments', details: String(err) }, 500);
  }
});

// ── Auth ───────────────────────────────────────────────────────────────────────

app.post('/requests', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ title?: string; description?: string; category?: string }>();
    if (!body.title?.trim()) return c.json({ error: 'title is required' }, 400);
    if (!body.description?.trim()) return c.json({ error: 'description is required' }, 400);
    if (body.category && !CATEGORIES.includes(body.category as FeatureCategory))
      return c.json({ error: `category must be one of: ${CATEGORIES.join(', ')}` }, 400);

    const request = await createRequest(
      c.env.DB, tenantId, body.title.trim(), body.description.trim(),
      (body.category as FeatureCategory) ?? 'general',
    );
    return c.json({ ok: true, data: request }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to submit feature request', details: String(err) }, 500);
  }
});

app.post('/requests/:requestId/vote', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const requestId = c.req.param('requestId');
    if (!await getRequest(c.env.DB, requestId)) return c.json({ error: 'Feature request not found' }, 404);
    const voted = await voteForRequest(c.env.DB, requestId, tenantId);
    return c.json({ ok: true, voted, message: voted ? 'Vote recorded' : 'Already voted' });
  } catch (err) {
    return c.json({ error: 'Failed to record vote', details: String(err) }, 500);
  }
});

app.delete('/requests/:requestId/vote', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const requestId = c.req.param('requestId');
    if (!await getRequest(c.env.DB, requestId)) return c.json({ error: 'Feature request not found' }, 404);
    const removed = await removeVote(c.env.DB, requestId, tenantId);
    return c.json({ ok: true, removed, message: removed ? 'Vote removed' : 'No vote to remove' });
  } catch (err) {
    return c.json({ error: 'Failed to remove vote', details: String(err) }, 500);
  }
});

app.post('/requests/:requestId/comments', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const requestId = c.req.param('requestId');
    const body = await c.req.json<{ content?: string }>();
    if (!body.content?.trim()) return c.json({ error: 'content is required' }, 400);
    if (!await getRequest(c.env.DB, requestId)) return c.json({ error: 'Feature request not found' }, 404);
    const comment = await addComment(c.env.DB, requestId, tenantId, body.content.trim(), false);
    return c.json({ ok: true, data: comment }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to add comment', details: String(err) }, 500);
  }
});

// ── Admin ──────────────────────────────────────────────────────────────────────

app.put('/admin/requests/:requestId', requireAdminKey, async (c) => {
  try {
    const requestId = c.req.param('requestId');
    const body = (await c.req.json<Record<string, unknown>>().catch(() => ({}))) as Record<string, unknown>;
    if (!await getRequest(c.env.DB, requestId)) return c.json({ error: 'Feature request not found' }, 404);

    if (body.status && !STATUSES.includes(body.status as FeatureStatus))
      return c.json({ error: `status must be one of: ${STATUSES.join(', ')}` }, 400);
    if (body.priority && !PRIORITIES.includes(body.priority as FeaturePriority))
      return c.json({ error: `priority must be one of: ${PRIORITIES.join(', ')}` }, 400);

    const allowed = ['status', 'priority', 'admin_response', 'planned_version', 'completed_at'] as const;
    const updates: Record<string, unknown> = {};
    for (const field of allowed) if (field in body) updates[field] = body[field];

    const updated = await updateRequestStatus(c.env.DB, requestId, updates as any);
    return c.json({ ok: true, data: updated });
  } catch (err) {
    return c.json({ error: 'Failed to update feature request', details: String(err) }, 500);
  }
});

app.get('/admin/overview', requireAdminKey, async (c) => {
  try {
    const overview = await getAdminFeatureOverview(c.env.DB);
    return c.json({ ok: true, data: overview });
  } catch (err) {
    return c.json({ error: 'Failed to fetch overview', details: String(err) }, 500);
  }
});

export { app as platformFeatureRequests };
