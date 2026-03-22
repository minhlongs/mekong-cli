/**
 * Tenant Access Tokens routes — create, introspect, revoke, refresh, admin
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantAccessTokensService } from '../services/tenant-access-tokens-service';

const app = new Hono<{ Bindings: Env }>();

// ── Admin auth helper ──────────────────────────────────────────────────────────

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Tenant routes (JWT / API key auth) ────────────────────────────────────────

/**
 * POST /v1/tenant-access-tokens/tokens — Create new access + refresh token pair
 */
app.post('/tokens', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    scopes?: string[];
    expires_in_days?: number;
    token_type?: string;
    created_by?: string;
    metadata?: Record<string, unknown>;
  };

  try {
    const result = await tenantAccessTokensService.createToken(c.env.DB, tenant.tenantId, body);
    return json({ ...result }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to create token', details: String(err) }, { status: 500 });
  }
});

/**
 * DELETE /v1/tenant-access-tokens/tokens/:id — Revoke a specific token
 */
app.delete('/tokens/:id', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');

  try {
    const result = await tenantAccessTokensService.revokeToken(c.env.DB, tenant.tenantId, id);
    return json(result);
  } catch (err) {
    return json({ error: 'Failed to revoke token', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /v1/tenant-access-tokens/tokens — List all tokens for tenant
 */
app.get('/tokens', auth(), async (c) => {
  const tenant = getTenant(c);

  try {
    const tokens = await tenantAccessTokensService.listTokens(c.env.DB, tenant.tenantId);
    return json({ tokens, total: tokens.length });
  } catch (err) {
    return json({ error: 'Failed to list tokens', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /v1/tenant-access-tokens/tokens/:id/usage — Get usage stats for a token
 */
app.get('/tokens/:id/usage', auth(), async (c) => {
  const tenant = getTenant(c);
  const id = c.req.param('id');

  try {
    const usage = await tenantAccessTokensService.getTokenUsage(c.env.DB, tenant.tenantId, id);
    if (!usage) return json({ error: 'Token not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ usage });
  } catch (err) {
    return json({ error: 'Failed to get token usage', details: String(err) }, { status: 500 });
  }
});

/**
 * POST /v1/tenant-access-tokens/revoke-all — Revoke all tokens for tenant
 */
app.post('/revoke-all', auth(), async (c) => {
  const tenant = getTenant(c);

  try {
    const result = await tenantAccessTokensService.revokeAllTokens(c.env.DB, tenant.tenantId);
    return json(result);
  } catch (err) {
    return json({ error: 'Failed to revoke all tokens', details: String(err) }, { status: 500 });
  }
});

// ── Public routes (no auth) ───────────────────────────────────────────────────

/**
 * POST /v1/tenant-access-tokens/introspect — Validate a token by hash
 * Body: { token: string }
 */
app.post('/introspect', async (c) => {
  const body = await c.req.json().catch(() => ({})) as { token?: string };
  if (!body.token) return json({ error: 'token is required' }, { status: 400 });

  try {
    const result = await tenantAccessTokensService.introspectToken(c.env.DB, body.token);
    return json(result);
  } catch (err) {
    return json({ error: 'Introspection failed', details: String(err) }, { status: 500 });
  }
});

/**
 * POST /v1/tenant-access-tokens/refresh — Exchange refresh token for new pair
 * Body: { refresh_token: string }
 */
app.post('/refresh', async (c) => {
  const body = await c.req.json().catch(() => ({})) as { refresh_token?: string };
  if (!body.refresh_token) return json({ error: 'refresh_token is required' }, { status: 400 });

  try {
    const result = await tenantAccessTokensService.refreshToken(c.env.DB, body.refresh_token);
    if (!result) return json({ error: 'Invalid or expired refresh token', code: 'INVALID_TOKEN' }, { status: 401 });
    return json(result);
  } catch (err) {
    return json({ error: 'Token refresh failed', details: String(err) }, { status: 500 });
  }
});

// ── Admin routes (X-Admin-Key) ────────────────────────────────────────────────

/**
 * POST /v1/tenant-access-tokens/cleanup — Delete expired and revoked tokens
 */
app.post('/cleanup', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Unauthorized' }, { status: 401 });

  try {
    const result = await tenantAccessTokensService.cleanupExpired(c.env.DB);
    return json(result);
  } catch (err) {
    return json({ error: 'Cleanup failed', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /v1/tenant-access-tokens/admin/overview — Token activity across all tenants
 */
app.get('/admin/overview', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Unauthorized' }, { status: 401 });

  try {
    const overview = await tenantAccessTokensService.getAdminOverview(c.env.DB);
    return json(overview);
  } catch (err) {
    return json({ error: 'Failed to get admin overview', details: String(err) }, { status: 500 });
  }
});

export { app as tenantAccessTokens };
