/**
 * API Rate Limit Policies routes — per-endpoint policies, templates, violations
 *
 * Mount path: /v1/rate-policies
 *
 * Tenant (auth):
 *   GET    /policies            — list policies
 *   POST   /policies            — create policy
 *   PUT    /policies/:id        — update policy
 *   DELETE /policies/:id        — delete policy
 *   POST   /apply-template      — apply template to tenant
 *   GET    /violations          — violation history
 *   GET    /stats               — policy stats
 *
 * Public:
 *   GET    /templates           — list templates
 *
 * Admin (X-Admin-Key):
 *   POST   /templates           — create template
 *   GET    /admin/overview      — platform overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  listPolicies,
  createPolicy,
  updatePolicy,
  deletePolicy,
  listTemplates,
  createTemplate,
  applyTemplate,
  getViolations,
  getPolicyStats,
  getAdminOverview,
} from '../services/api-rate-limit-policies-service';

const app = new Hono<{ Bindings: Env }>();

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

// ---------------------------------------------------------------------------
// Policies (auth)
// ---------------------------------------------------------------------------

app.get('/policies', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const policies = await listPolicies(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data: policies });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

app.post('/policies', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.policy_name || !body.endpoint_pattern) {
    return json({ error: 'policy_name and endpoint_pattern required', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const result = await createPolicy(c.env.DB, tenant.tenantId, body as never);
    return c.json({ success: true, data: result }, 201);
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

app.put('/policies/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const updated = await updatePolicy(c.env.DB, id, tenant.tenantId, body as never);
    if (!updated) return json({ error: 'Policy not found', code: 'NOT_FOUND' }, { status: 404 });
    return c.json({ success: true, data: { id } });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

app.delete('/policies/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');
  try {
    const deleted = await deletePolicy(c.env.DB, id, tenant.tenantId);
    if (!deleted) return json({ error: 'Policy not found', code: 'NOT_FOUND' }, { status: 404 });
    return c.json({ success: true, data: { id } });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

app.get('/templates', async (c) => {
  try {
    const templates = await listTemplates(c.env.DB);
    return c.json({ success: true, data: templates });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

app.post('/templates', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.template_name || !body.policies_json) {
    return json({ error: 'template_name and policies_json required', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const result = await createTemplate(c.env.DB, body as never);
    return c.json({ success: true, data: result }, 201);
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Apply template + violations + stats (auth)
// ---------------------------------------------------------------------------

app.post('/apply-template', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.template_id) {
    return json({ error: 'template_id required', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const result = await applyTemplate(c.env.DB, tenant.tenantId, body.template_id as string);
    return c.json({ success: true, data: { tenant_id: tenant.tenantId, ...result } });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Apply failed';
    const status = msg === 'Template not found' ? 404 : 500;
    return json({ error: msg, code: status === 404 ? 'NOT_FOUND' : 'DB_ERROR' }, { status });
  }
});

app.get('/violations', auth(), async (c) => {
  const tenant = getTenant(c);
  const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '50', 10), 1), 200);
  try {
    const violations = await getViolations(c.env.DB, tenant.tenantId, limit);
    return c.json({ success: true, data: { tenant_id: tenant.tenantId, violations } });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

app.get('/stats', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const stats = await getPolicyStats(c.env.DB, tenant.tenantId);
    return c.json({ success: true, data: { tenant_id: tenant.tenantId, ...stats } });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  try {
    const overview = await getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'DB error', code: 'DB_ERROR' }, { status: 500 });
  }
});

export { app as apiRateLimitPolicies };
