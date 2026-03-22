/**
 * Tenant Custom Domains routes
 * Mount at: /v1/domains
 *
 * GET  /domains            — list tenant's custom domains
 * POST /domains            — register a new custom domain
 * GET  /verifications      — get verifications for a domain (query: domain_id)
 * GET  /admin/overview     — platform-wide domain stats (admin key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantCustomDomainsService } from '../services/tenant-custom-domains';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
  [key: string]: any;
};

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /domains — list all custom domains for authenticated tenant
 */
app.get('/domains', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantCustomDomainsService.listDomains(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    console.error('[GET /domains] error:', err);
    return c.json({ error: 'Failed to list domains' }, 500);
  }
});

/**
 * POST /domains — register a new custom domain
 * Body: { domain: string, dns_record?: string }
 */
app.post('/domains', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({}));

    if (!body.domain || typeof body.domain !== 'string') {
      return c.json({ error: 'domain is required' }, 400);
    }

    const result = await tenantCustomDomainsService.createDomain(
      c.env.DB,
      tenantId,
      body.domain.trim().toLowerCase(),
      body.dns_record
    );

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result, 201);
  } catch (err) {
    console.error('[POST /domains] error:', err);
    return c.json({ error: 'Failed to create domain' }, 500);
  }
});

/**
 * GET /verifications — get verification records for a domain
 * Query param: domain_id (required)
 */
app.get('/verifications', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const domainId = c.req.query('domain_id');

    if (!domainId) {
      return c.json({ error: 'domain_id query param is required' }, 400);
    }

    const result = await tenantCustomDomainsService.getVerifications(
      c.env.DB,
      tenantId,
      domainId
    );

    if (!result.success) return c.json({ error: result.error }, result.error === 'Domain not found' ? 404 : 500);
    return c.json(result);
  } catch (err) {
    console.error('[GET /verifications] error:', err);
    return c.json({ error: 'Failed to get verifications' }, 500);
  }
});

/**
 * GET /admin/overview — platform-wide domain stats
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var
 */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!c.env.ADMIN_API_KEY || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await tenantCustomDomainsService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    console.error('[GET /admin/overview] error:', err);
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantCustomDomains };
