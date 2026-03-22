/**
 * Tenant API Tokens Routes
 * Long-lived service tokens with scoped permissions, rotation, and expiry management.
 *
 * GET    /tokens               — list tokens (auth)
 * POST   /tokens               — create token (auth)
 * GET    /tokens/:tokenId      — get token detail (auth)
 * DELETE /tokens/:tokenId      — revoke token (auth)
 * POST   /tokens/:tokenId/rotate — rotate token (auth)
 * POST   /validate             — validate token (public)
 * GET    /admin/overview       — admin stats (X-Admin-Key)
 * POST   /admin/cleanup        — clean expired tokens (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createToken,
  listTokens,
  getToken,
  revokeToken,
  rotateToken,
  validateToken,
  updateLastUsed,
  getAdminTokenOverview,
  cleanExpiredTokens,
  type TokenScope,
} from '../services/tenant-api-tokens-service';

const VALID_SCOPES: TokenScope[] = ['read', 'write', 'admin', 'missions', 'billing'];

function validateScopes(input: unknown): TokenScope[] {
  if (!Array.isArray(input)) return ['read'];
  return input.filter((s): s is TokenScope => VALID_SCOPES.includes(s as TokenScope));
}

/** Hash plaintext token for lookup */
async function hashForLookup(token: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

export const tenantApiTokens = new Hono<{ Bindings: Env }>();

// GET /tokens — list all tokens for authenticated tenant
tenantApiTokens.get('/tokens', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const tokens = await listTokens(c.env.DB, tenantId);
    return c.json({ tokens, total: tokens.length });
  } catch (err) {
    return c.json({ error: 'Failed to list tokens' }, 500);
  }
});

// POST /tokens — create new token
tenantApiTokens.post('/tokens', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as {
      name?: string;
      scopes?: unknown;
      expires_in?: number;
    };

    const name = body.name?.trim();
    if (!name) return c.json({ error: 'name is required', code: 'VALIDATION_ERROR' }, 400);

    const scopes = validateScopes(body.scopes);
    if (!scopes.length) return c.json({ error: 'At least one valid scope required', code: 'VALIDATION_ERROR' }, 400);

    const expiresIn = typeof body.expires_in === 'number' && body.expires_in > 0
      ? body.expires_in
      : undefined;

    const { token, plaintext } = await createToken(c.env.DB, tenantId, name, scopes, expiresIn);

    return c.json({
      ...token,
      token: plaintext,
      hint: 'Store this token securely — it will not be shown again',
    }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create token' }, 500);
  }
});

// GET /tokens/:tokenId — get token detail
tenantApiTokens.get('/tokens/:tokenId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const token = await getToken(c.env.DB, tenantId, c.req.param('tokenId'));
    if (!token) return c.json({ error: 'Token not found', code: 'NOT_FOUND' }, 404);
    return c.json(token);
  } catch (err) {
    return c.json({ error: 'Failed to get token' }, 500);
  }
});

// DELETE /tokens/:tokenId — revoke token
tenantApiTokens.delete('/tokens/:tokenId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const revoked = await revokeToken(c.env.DB, tenantId, c.req.param('tokenId'));
    if (!revoked) return c.json({ error: 'Token not found or already revoked', code: 'NOT_FOUND' }, 404);
    return c.json({ success: true, message: 'Token revoked' });
  } catch (err) {
    return c.json({ error: 'Failed to revoke token' }, 500);
  }
});

// POST /tokens/:tokenId/rotate — rotate token
tenantApiTokens.post('/tokens/:tokenId/rotate', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await rotateToken(c.env.DB, tenantId, c.req.param('tokenId'));
    if (!result) return c.json({ error: 'Token not found or inactive', code: 'NOT_FOUND' }, 404);

    return c.json({
      ...result.token,
      token: result.plaintext,
      hint: 'Previous token has been revoked — store this new token securely',
    }, 201);
  } catch (err) {
    return c.json({ error: 'Failed to rotate token' }, 500);
  }
});

// POST /validate — validate token (internal/public endpoint)
tenantApiTokens.post('/validate', async (c) => {
  try {
    const body = await c.req.json().catch(() => ({})) as { token?: string };
    if (!body.token) return c.json({ error: 'token is required', code: 'VALIDATION_ERROR' }, 400);

    const hash = await hashForLookup(body.token);
    const token = await validateToken(c.env.DB, hash);

    if (!token) return c.json({ valid: false, error: 'Invalid or expired token' }, 401);

    // Update last used metadata (non-blocking)
    const ip = c.req.header('CF-Connecting-IP') ?? c.req.header('X-Forwarded-For') ?? 'unknown';
    updateLastUsed(c.env.DB, token.id, ip).catch(() => {});

    return c.json({
      valid: true,
      tenant_id: token.tenant_id,
      token_id: token.id,
      scopes: token.scopes,
      expires_at: token.expires_at,
    });
  } catch (err) {
    return c.json({ error: 'Validation failed' }, 500);
  }
});

// GET /admin/overview — admin stats
tenantApiTokens.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden', code: 'FORBIDDEN' }, 403);
  }

  try {
    const overview = await getAdminTokenOverview(c.env.DB);
    return c.json(overview);
  } catch (err) {
    return c.json({ error: 'Failed to get overview' }, 500);
  }
});

// POST /admin/cleanup — deactivate expired tokens
tenantApiTokens.post('/admin/cleanup', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden', code: 'FORBIDDEN' }, 403);
  }

  try {
    const cleaned = await cleanExpiredTokens(c.env.DB);
    return c.json({ success: true, tokens_deactivated: cleaned });
  } catch (err) {
    return c.json({ error: 'Cleanup failed' }, 500);
  }
});
