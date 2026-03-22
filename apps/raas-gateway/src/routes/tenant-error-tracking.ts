/**
 * Tenant Error Tracking routes — log and query error entries and rules
 * Auth: GET /errors, POST /errors, GET /rules
 * Admin: GET /admin/overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantErrorTrackingService } from '../services/tenant-error-tracking';

const app = new Hono<{ Bindings: Env }>();

// ── Admin helper ────────────────────────────────────────────────────────────────

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Auth routes ─────────────────────────────────────────────────────────────────

/**
 * GET /errors — list recent error entries for authenticated tenant
 * Query: limit (default 50, max 200)
 */
app.get('/errors', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200);
  try {
    const result = await tenantErrorTrackingService.listErrors(c.env.DB, tenantId, limit);
    if (!result.success) return c.json({ error: result.error }, 500);
    return json({ errors: result.data, total: result.data?.length ?? 0 });
  } catch (err) {
    return c.json({ error: 'Failed to list errors', details: String(err) }, 500);
  }
});

/**
 * POST /errors — create a new error entry for authenticated tenant
 * Body: { error_type, message, stack_trace?, endpoint?, status_code? }
 */
app.post('/errors', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

  const errorType = String(body.error_type ?? '').trim();
  const message = String(body.message ?? '').trim();

  if (!errorType) {
    return json({ error: 'error_type is required', code: 'INVALID_INPUT' }, { status: 400 });
  }
  if (!message) {
    return json({ error: 'message is required', code: 'INVALID_INPUT' }, { status: 400 });
  }

  const stackTrace = body.stack_trace ? String(body.stack_trace) : undefined;
  const endpoint = body.endpoint ? String(body.endpoint) : undefined;
  const statusCode = body.status_code !== undefined ? Number(body.status_code) : undefined;

  try {
    const result = await tenantErrorTrackingService.createError(
      c.env.DB, tenantId, errorType, message, stackTrace, endpoint, statusCode
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return json({ error: result.data }, { status: 201 });
  } catch (err) {
    return c.json({ error: 'Failed to create error entry', details: String(err) }, 500);
  }
});

/**
 * GET /rules — list error rules for authenticated tenant
 */
app.get('/rules', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const result = await tenantErrorTrackingService.getRules(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return json({ rules: result.data, total: result.data?.length ?? 0 });
  } catch (err) {
    return c.json({ error: 'Failed to list error rules', details: String(err) }, 500);
  }
});

// ── Admin route ─────────────────────────────────────────────────────────────────

/**
 * GET /admin/overview — platform-wide error stats (X-Admin-Key required)
 */
app.get('/admin/overview', async (c) => {
  if (!requireAdminKey(c)) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await tenantErrorTrackingService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return json(result.data);
  } catch (err) {
    return c.json({ error: 'Failed to fetch admin overview', details: String(err) }, 500);
  }
});

export { app as tenantErrorTracking };
