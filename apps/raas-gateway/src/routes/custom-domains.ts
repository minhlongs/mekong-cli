/**
 * Custom domains routes — enterprise tenant white-label API domain management
 * Tenant endpoints require auth; admin endpoints require X-Admin-Key header
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  addDomain,
  listDomains,
  getDomain,
  verifyDomain,
  removeDomain,
  getDomainByHostname,
  getDomainStats,
  getAdminDomainOverview,
  cleanExpiredVerifications,
} from '../services/custom-domains-service';

export const customDomains = new Hono<{ Bindings: Env }>();

/** GET /domains — list all custom domains for authenticated tenant */
customDomains.get('/domains', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const domains = await listDomains(c.env.DB, tenantId);
    return json({ domains, total: domains.length });
  } catch {
    return json({ error: 'Failed to list domains', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** POST /domains — register a new custom domain for authenticated tenant */
customDomains.post('/domains', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const { domain } = body as { domain?: string };

  if (!domain || typeof domain !== 'string' || domain.trim().length === 0) {
    return json({ error: 'domain is required', code: 'INVALID_INPUT' }, { status: 400 });
  }

  // Basic domain format validation
  const domainPattern = /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$/;
  if (!domainPattern.test(domain.trim())) {
    return json({ error: 'Invalid domain format', code: 'INVALID_INPUT' }, { status: 400 });
  }

  try {
    const record = await addDomain(c.env.DB, tenantId, domain.trim());
    return json(
      {
        domain: record,
        message: 'Domain registered. Add CNAME or TXT record to verify ownership.',
        verification: {
          method: record.verification_method,
          token: record.verification_token,
          cname_target: 'domains.mekong-raas.io',
          txt_record: `_mekong-verify.${record.domain}`,
        },
      },
      { status: 201 }
    );
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to add domain';
    const isDupe = msg.toLowerCase().includes('already registered');
    return json({ error: msg, code: isDupe ? 'CONFLICT' : 'INTERNAL_ERROR' }, { status: isDupe ? 409 : 500 });
  }
});

/** GET /domains/:id — get domain detail for authenticated tenant */
customDomains.get('/domains/:id', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const id = c.req.param('id');

  const domain = await getDomain(c.env.DB, tenantId, id);
  if (!domain) {
    return json({ error: 'Domain not found', code: 'NOT_FOUND' }, { status: 404 });
  }
  return json({ domain });
});

/** POST /domains/:id/verify — trigger DNS verification for a domain */
customDomains.post('/domains/:id/verify', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const id = c.req.param('id');

  const existing = await getDomain(c.env.DB, tenantId, id);
  if (!existing) {
    return json({ error: 'Domain not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  if (existing.status === 'active') {
    return json({ domain: existing, message: 'Domain already verified and active' });
  }

  const updated = await verifyDomain(c.env.DB, tenantId, id);
  if (!updated) {
    return json({ error: 'Verification failed', code: 'INTERNAL_ERROR' }, { status: 500 });
  }

  return json({
    domain: updated,
    message: updated.status === 'active'
      ? 'Domain verified successfully'
      : 'Verification initiated — DNS propagation may take up to 48 hours',
  });
});

/** DELETE /domains/:id — remove a custom domain */
customDomains.delete('/domains/:id', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const id = c.req.param('id');

  const existing = await getDomain(c.env.DB, tenantId, id);
  if (!existing) {
    return json({ error: 'Domain not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  const deleted = await removeDomain(c.env.DB, tenantId, id);
  if (!deleted) {
    return json({ error: 'Failed to remove domain', code: 'INTERNAL_ERROR' }, { status: 500 });
  }

  return json({ message: 'Domain removed successfully', id });
});

/** GET /stats — domain counts by status for authenticated tenant */
customDomains.get('/stats', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const stats = await getDomainStats(c.env.DB, tenantId);
    return json({ stats });
  } catch {
    return json({ error: 'Failed to fetch stats', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** GET /lookup/:hostname — resolve tenant by hostname (public, used by edge router) */
customDomains.get('/lookup/:hostname', async (c) => {
  const hostname = c.req.param('hostname');
  if (!hostname) {
    return json({ error: 'hostname required', code: 'INVALID_INPUT' }, { status: 400 });
  }

  const domain = await getDomainByHostname(c.env.DB, hostname);
  if (!domain) {
    return json({ error: 'Hostname not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  // Return only safe routing info — no verification tokens
  return json({
    tenant_id: domain.tenant_id,
    domain: domain.domain,
    ssl_status: domain.ssl_status,
  });
});

/** GET /admin/overview — all domains grouped by status (admin only) */
customDomains.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  }

  try {
    const overview = await getAdminDomainOverview(c.env.DB);
    const total = overview.reduce((sum, row) => sum + row.count, 0);
    return json({ overview, total });
  } catch {
    return json({ error: 'Failed to fetch overview', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

/** POST /admin/cleanup — remove unverified domains older than 7 days (admin only) */
customDomains.post('/admin/cleanup', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  }

  try {
    const removed = await cleanExpiredVerifications(c.env.DB);
    return json({ removed, message: `Cleaned ${removed} expired verification(s)` });
  } catch {
    return json({ error: 'Cleanup failed', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});
