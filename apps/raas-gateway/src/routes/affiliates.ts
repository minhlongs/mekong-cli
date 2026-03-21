/**
 * Affiliate routes — partner registration, commission tracking, admin management
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  registerPartner,
  getPartnerStats,
  getCommissions,
  getLeaderboard,
  approveCommissions,
  adminGetAllPartners,
} from '../services/affiliate-service';

export const affiliates = new Hono<{ Bindings: Env }>();

// ── Admin auth helper ──────────────────────────────────────────────────────────

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Tenant routes (JWT / API key auth) ────────────────────────────────────────

/**
 * POST /v1/affiliates/register — Register authenticated tenant as affiliate partner
 */
affiliates.post('/register', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as { payout_method?: string };

  try {
    const partner = await registerPartner(c.env.DB, tenant.tenantId, body.payout_method);
    return json({ partner });
  } catch (err) {
    return json({ error: 'Failed to register partner', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /v1/affiliates/stats — Get own partner stats
 */
affiliates.get('/stats', auth(), async (c) => {
  const tenant = getTenant(c);

  const partner = await getPartnerStats(c.env.DB, tenant.tenantId);
  if (!partner) {
    return json({ error: 'Not registered as affiliate partner', code: 'NOT_FOUND' }, { status: 404 });
  }

  return json({ partner });
});

/**
 * GET /v1/affiliates/commissions — List own commissions (optional ?status= filter)
 */
affiliates.get('/commissions', auth(), async (c) => {
  const tenant = getTenant(c);
  const status = c.req.query('status');

  const partner = await getPartnerStats(c.env.DB, tenant.tenantId);
  if (!partner) {
    return json({ error: 'Not registered as affiliate partner', code: 'NOT_FOUND' }, { status: 404 });
  }

  const commissions = await getCommissions(c.env.DB, partner.id, status);
  return json({ commissions, total: commissions.length });
});

/**
 * GET /v1/affiliates/referrals — List own referrals
 */
affiliates.get('/referrals', auth(), async (c) => {
  const tenant = getTenant(c);

  const partner = await getPartnerStats(c.env.DB, tenant.tenantId);
  if (!partner) {
    return json({ error: 'Not registered as affiliate partner', code: 'NOT_FOUND' }, { status: 404 });
  }

  const result = await c.env.DB.prepare(
    'SELECT * FROM affiliate_referrals WHERE partner_id = ? ORDER BY signup_at DESC'
  ).bind(partner.id).all<Record<string, unknown>>();

  return json({ referrals: result.results ?? [], total: result.results?.length ?? 0 });
});

// ── Admin routes (X-Admin-Key) ─────────────────────────────────────────────────

/**
 * GET /admin/affiliates — List all partners
 */
affiliates.get('/admin', async (c) => {
  if (!requireAdminKey(c)) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }

  const partners = await adminGetAllPartners(c.env.DB);
  return json({ partners, total: partners.length });
});

/**
 * GET /admin/affiliates/leaderboard — Top earners
 */
affiliates.get('/admin/leaderboard', async (c) => {
  if (!requireAdminKey(c)) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }

  const limit = Math.min(Number(c.req.query('limit') ?? 10), 50);
  const leaderboard = await getLeaderboard(c.env.DB, limit);
  return json({ leaderboard });
});

/**
 * POST /admin/affiliates/:id/approve-commissions — Approve pending commissions
 */
affiliates.post('/admin/:id/approve-commissions', async (c) => {
  if (!requireAdminKey(c)) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await c.req.json().catch(() => ({})) as { commission_ids?: string[] };
  if (!Array.isArray(body.commission_ids) || !body.commission_ids.length) {
    return json({ error: 'commission_ids array required', code: 'INVALID_INPUT' }, { status: 400 });
  }

  const result = await approveCommissions(c.env.DB, body.commission_ids);
  return json({ approved: result.approved });
});

/**
 * PUT /admin/affiliates/:id/status — Update partner status (active/suspended/terminated)
 */
affiliates.put('/admin/:id/status', async (c) => {
  if (!requireAdminKey(c)) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }

  const partnerId = c.req.param('id');
  const body = await c.req.json().catch(() => ({})) as { status?: string };
  const allowed = ['active', 'suspended', 'terminated'];

  if (!body.status || !allowed.includes(body.status)) {
    return json({ error: `status must be one of: ${allowed.join(', ')}`, code: 'INVALID_INPUT' }, { status: 400 });
  }

  const result = await c.env.DB.prepare(
    `UPDATE affiliate_partners SET status = ?, updated_at = datetime('now') WHERE id = ?`
  ).bind(body.status, partnerId).run();

  if (!result.meta?.changes) {
    return json({ error: 'Partner not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  return json({ success: true, status: body.status });
});
