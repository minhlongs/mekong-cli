/**
 * Marketplace Payment Routes — /v1/marketplace-payments
 * Revenue share endpoints for template sellers: register, transact, payout
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  registerSeller,
  getSellerProfile,
  updateSellerProfile,
  recordPurchase,
  getSellerTransactions,
  getSellerEarnings,
  requestPayout,
  getPayouts,
  processPayouts,
  getMarketplaceStats,
} from '../services/marketplace-payment-service';

export const marketplacePayments = new Hono<{ Bindings: Env }>();

// ── Admin auth helper ──────────────────────────────────────────────────────────

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Seller registration (must be before /sellers/me catch-all) ────────────────

/**
 * POST /sellers/register — Register authenticated tenant as marketplace seller
 */
marketplacePayments.post('/sellers/register', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as { display_name?: string; payout_email?: string };

  if (!body.display_name) {
    return json({ error: 'display_name is required' }, { status: 400 });
  }

  try {
    const seller = await registerSeller(c.env.DB, tenant.tenantId, {
      display_name: body.display_name,
      payout_email: body.payout_email,
    });
    return json({ seller });
  } catch (err) {
    return json({ error: 'Failed to register seller', details: String(err) }, { status: 500 });
  }
});

// ── Seller self-service routes ─────────────────────────────────────────────────

/**
 * GET /sellers/me — Get own seller profile
 */
marketplacePayments.get('/sellers/me', auth(), async (c) => {
  const tenant = getTenant(c);
  const seller = await getSellerProfile(c.env.DB, tenant.tenantId);
  if (!seller) return json({ error: 'Not registered as seller', code: 'NOT_FOUND' }, { status: 404 });
  return json({ seller });
});

/**
 * PUT /sellers/me — Update display name or payout email
 */
marketplacePayments.put('/sellers/me', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as { display_name?: string; payout_email?: string };

  try {
    const seller = await updateSellerProfile(c.env.DB, tenant.tenantId, body);
    if (!seller) return json({ error: 'Not registered as seller', code: 'NOT_FOUND' }, { status: 404 });
    return json({ seller });
  } catch (err) {
    return json({ error: 'Failed to update profile', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /sellers/me/transactions — List own transactions (supports ?limit=&offset=)
 */
marketplacePayments.get('/sellers/me/transactions', auth(), async (c) => {
  const tenant = getTenant(c);
  const seller = await getSellerProfile(c.env.DB, tenant.tenantId);
  if (!seller) return json({ error: 'Not registered as seller', code: 'NOT_FOUND' }, { status: 404 });

  const limit = parseInt(c.req.query('limit') ?? '50', 10);
  const offset = parseInt(c.req.query('offset') ?? '0', 10);

  try {
    const transactions = await getSellerTransactions(c.env.DB, seller.id, { limit, offset });
    return json({ transactions, total: transactions.length });
  } catch (err) {
    return json({ error: 'Failed to fetch transactions', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /sellers/me/earnings — Earnings summary with available balance
 */
marketplacePayments.get('/sellers/me/earnings', auth(), async (c) => {
  const tenant = getTenant(c);
  const seller = await getSellerProfile(c.env.DB, tenant.tenantId);
  if (!seller) return json({ error: 'Not registered as seller', code: 'NOT_FOUND' }, { status: 404 });

  try {
    const earnings = await getSellerEarnings(c.env.DB, seller.id);
    return json({ earnings });
  } catch (err) {
    return json({ error: 'Failed to fetch earnings', details: String(err) }, { status: 500 });
  }
});

/**
 * POST /sellers/me/payouts — Request payout (body: { amount })
 */
marketplacePayments.post('/sellers/me/payouts', auth(), async (c) => {
  const tenant = getTenant(c);
  const seller = await getSellerProfile(c.env.DB, tenant.tenantId);
  if (!seller) return json({ error: 'Not registered as seller', code: 'NOT_FOUND' }, { status: 404 });

  const body = await c.req.json().catch(() => ({})) as { amount?: number };
  if (!body.amount || body.amount <= 0) {
    return json({ error: 'Valid amount is required' }, { status: 400 });
  }

  try {
    const result = await requestPayout(c.env.DB, seller.id, body.amount);
    if (!result.success) return json({ error: result.error }, { status: 400 });
    return json({ payout: result.payout }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to request payout', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /sellers/me/payouts — Payout history
 */
marketplacePayments.get('/sellers/me/payouts', auth(), async (c) => {
  const tenant = getTenant(c);
  const seller = await getSellerProfile(c.env.DB, tenant.tenantId);
  if (!seller) return json({ error: 'Not registered as seller', code: 'NOT_FOUND' }, { status: 404 });

  try {
    const payouts = await getPayouts(c.env.DB, seller.id);
    return json({ payouts, total: payouts.length });
  } catch (err) {
    return json({ error: 'Failed to fetch payouts', details: String(err) }, { status: 500 });
  }
});

// ── Purchase recording ─────────────────────────────────────────────────────────

/**
 * POST /purchase — Record template purchase (auth, body: { templateId, amount, sellerId })
 */
marketplacePayments.post('/purchase', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    templateId?: string; amount?: number; sellerId?: string;
  };

  if (!body.templateId || !body.amount || !body.sellerId) {
    return json({ error: 'templateId, amount, and sellerId are required' }, { status: 400 });
  }
  if (body.amount <= 0) {
    return json({ error: 'amount must be positive' }, { status: 400 });
  }

  try {
    const seller = await c.env.DB.prepare('SELECT * FROM marketplace_sellers WHERE id = ? AND status = ?')
      .bind(body.sellerId, 'active').first<{ id: string; commission_rate: number }>();
    if (!seller) return json({ error: 'Seller not found or inactive', code: 'NOT_FOUND' }, { status: 404 });

    const transaction = await recordPurchase(
      c.env.DB, seller.id, tenant.tenantId, body.templateId, body.amount, seller.commission_rate
    );
    return json({ transaction }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to record purchase', details: String(err) }, { status: 500 });
  }
});

// ── Admin routes ───────────────────────────────────────────────────────────────

/**
 * POST /admin/process-payouts — Mark all pending payouts as processing
 */
marketplacePayments.post('/admin/process-payouts', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Unauthorized' }, { status: 401 });

  try {
    const result = await processPayouts(c.env.DB);
    return json({ ...result, message: `${result.processed} payout(s) moved to processing` });
  } catch (err) {
    return json({ error: 'Failed to process payouts', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /admin/stats — Platform-wide marketplace statistics
 */
marketplacePayments.get('/admin/stats', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Unauthorized' }, { status: 401 });

  try {
    const stats = await getMarketplaceStats(c.env.DB);
    return json({ stats });
  } catch (err) {
    return json({ error: 'Failed to fetch stats', details: String(err) }, { status: 500 });
  }
});
