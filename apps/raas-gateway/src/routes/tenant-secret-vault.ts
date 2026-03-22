/**
 * Tenant Secret Vault routes — manage encrypted secrets per tenant
 * Mount at: /v1/secrets
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantSecretVaultService } from '../services/tenant-secret-vault-service';

export const tenantSecretVault = new Hono<{ Bindings: Env }>();

// All tenant routes require auth
tenantSecretVault.use('*', auth());

/**
 * GET /v1/secrets — list secrets for authenticated tenant (no encrypted values)
 */
tenantSecretVault.get('/secrets', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const secrets = await tenantSecretVaultService.listSecrets(c.env.DB, tenantId);
    return c.json({ success: true, data: secrets });
  } catch (err) {
    console.error('[secretVault GET /secrets] error:', err);
    return c.json({ success: false, error: 'Failed to list secrets' }, 500);
  }
});

/**
 * POST /v1/secrets — create a new secret for authenticated tenant
 * Body: { secret_name, encrypted_value, secret_type?, expires_at? }
 */
tenantSecretVault.post('/secrets', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body.secret_name || !body.encrypted_value) {
      return c.json({ success: false, error: 'secret_name and encrypted_value are required' }, 400);
    }
    const secret = await tenantSecretVaultService.createSecret(c.env.DB, tenantId, body);
    return c.json({ success: true, data: secret }, 201);
  } catch (err) {
    console.error('[secretVault POST /secrets] error:', err);
    return c.json({ success: false, error: 'Failed to create secret' }, 500);
  }
});

/**
 * GET /v1/secrets/access-logs — access audit log for authenticated tenant
 * Query param: secret_id (optional filter)
 */
tenantSecretVault.get('/access-logs', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const secretId = c.req.query('secret_id');
    const logs = await tenantSecretVaultService.getAccessLogs(c.env.DB, tenantId, secretId);
    return c.json({ success: true, data: logs });
  } catch (err) {
    console.error('[secretVault GET /access-logs] error:', err);
    return c.json({ success: false, error: 'Failed to fetch access logs' }, 500);
  }
});

/**
 * GET /v1/secrets/admin/overview — cross-tenant secret stats (admin only)
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
tenantSecretVault.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ success: false, error: 'Forbidden' }, 403);
    }
    const overview = await tenantSecretVaultService.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    console.error('[secretVault GET /admin/overview] error:', err);
    return c.json({ success: false, error: 'Failed to fetch admin overview' }, 500);
  }
});
