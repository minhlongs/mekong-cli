/**
 * API Sandbox routes — isolated test environments per tenant
 * NOTE: /stats and /execute mounted BEFORE /:id to avoid param shadowing
 *
 * GET    /environments        — listSandboxes
 * POST   /environments        — createSandbox
 * GET    /stats               — getSandboxStats
 * POST   /execute             — executeRequest
 * GET    /environments/:id    — getSandbox
 * DELETE /environments/:id    — deleteSandbox
 * POST   /environments/:id/mock   — setMockResponse
 * GET    /environments/:id/history — getRequestHistory
 * POST   /environments/:id/reset  — resetSandbox
 * DELETE /environments/:id/history — clearHistory
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createSandbox,
  listSandboxes,
  getSandbox,
  deleteSandbox,
  setMockResponse,
  executeRequest,
  getRequestHistory,
  clearHistory,
  getSandboxStats,
  resetSandbox,
} from '../services/api-sandbox-service';

const app = new Hono<{ Bindings: Env }>();
app.use('/*', auth());

// ── List sandboxes ────────────────────────────────────────────────────────────
app.get('/environments', async (c) => {
  const { tenantId } = getTenant(c);
  const sandboxes = await listSandboxes(c.env.DB, tenantId);
  return c.json({ success: true, data: sandboxes });
});

// ── Create sandbox ────────────────────────────────────────────────────────────
app.post('/environments', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const sandbox = await createSandbox(c.env.DB, tenantId, body.name || 'default', body.config);
  return c.json({ success: true, data: sandbox }, 201);
});

// ── Stats (BEFORE /:id) ───────────────────────────────────────────────────────
app.get('/stats', async (c) => {
  const { tenantId } = getTenant(c);
  const stats = await getSandboxStats(c.env.DB, tenantId);
  return c.json({ success: true, data: stats });
});

// ── Execute request (BEFORE /:id) ─────────────────────────────────────────────
app.post('/execute', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const { sandbox_id, method, path, body: reqBody } = body;
  if (!sandbox_id || !method || !path) {
    return c.json({ success: false, error: 'sandbox_id, method, and path are required' }, 400);
  }
  // Verify sandbox belongs to tenant
  const sandbox = await getSandbox(c.env.DB, sandbox_id, tenantId);
  if (!sandbox) return c.json({ success: false, error: 'Sandbox not found' }, 404);

  const result = await executeRequest(c.env.DB, sandbox_id, method, path, reqBody);
  return c.json({ success: true, data: result });
});

// ── Get single sandbox ────────────────────────────────────────────────────────
app.get('/environments/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const sandbox = await getSandbox(c.env.DB, c.req.param('id'), tenantId);
  if (!sandbox) return c.json({ success: false, error: 'Sandbox not found' }, 404);
  return c.json({ success: true, data: sandbox });
});

// ── Delete sandbox ────────────────────────────────────────────────────────────
app.delete('/environments/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const deleted = await deleteSandbox(c.env.DB, c.req.param('id'), tenantId);
  if (!deleted) return c.json({ success: false, error: 'Sandbox not found' }, 404);
  return c.json({ success: true, message: 'Sandbox deleted' });
});

// ── Set mock response ─────────────────────────────────────────────────────────
app.post('/environments/:id/mock', async (c) => {
  const { tenantId } = getTenant(c);
  const sandboxId = c.req.param('id');
  const sandbox = await getSandbox(c.env.DB, sandboxId, tenantId);
  if (!sandbox) return c.json({ success: false, error: 'Sandbox not found' }, 404);

  const body = await c.req.json().catch(() => ({}));
  const { path, method, status_code, body: respBody } = body;
  if (!path || !method || !status_code) {
    return c.json({ success: false, error: 'path, method, and status_code are required' }, 400);
  }
  await setMockResponse(c.env.DB, sandboxId, path, method, status_code, respBody ?? {});
  return c.json({ success: true, message: 'Mock response configured' });
});

// ── Get request history ───────────────────────────────────────────────────────
app.get('/environments/:id/history', async (c) => {
  const { tenantId } = getTenant(c);
  const sandboxId = c.req.param('id');
  const sandbox = await getSandbox(c.env.DB, sandboxId, tenantId);
  if (!sandbox) return c.json({ success: false, error: 'Sandbox not found' }, 404);

  const limit = parseInt(c.req.query('limit') ?? '50', 10);
  const history = await getRequestHistory(c.env.DB, sandboxId, limit);
  return c.json({ success: true, data: history });
});

// ── Reset sandbox ─────────────────────────────────────────────────────────────
app.post('/environments/:id/reset', async (c) => {
  const { tenantId } = getTenant(c);
  const sandboxId = c.req.param('id');
  const sandbox = await getSandbox(c.env.DB, sandboxId, tenantId);
  if (!sandbox) return c.json({ success: false, error: 'Sandbox not found' }, 404);

  await resetSandbox(c.env.DB, sandboxId);
  return c.json({ success: true, message: 'Sandbox reset' });
});

// ── Clear history ─────────────────────────────────────────────────────────────
app.delete('/environments/:id/history', async (c) => {
  const { tenantId } = getTenant(c);
  const sandboxId = c.req.param('id');
  const sandbox = await getSandbox(c.env.DB, sandboxId, tenantId);
  if (!sandbox) return c.json({ success: false, error: 'Sandbox not found' }, 404);

  await clearHistory(c.env.DB, sandboxId);
  return c.json({ success: true, message: 'History cleared' });
});

export { app as apiSandbox };
