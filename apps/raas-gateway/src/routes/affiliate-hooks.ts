/**
 * Affiliate Hooks Routes — internal webhooks for signup/payment events + partner dashboard
 * POST /hooks/signup   — called internally when tenant signs up with ?ref=CODE
 * POST /hooks/payment  — called internally when Polar confirms payment
 * GET  /partner/earnings — partner earnings dashboard (auth required)
 * POST /partner/payout   — request payout (auth required)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  processSignupReferral,
  processPaymentCommission,
  getPartnerEarnings,
  processCommissionPayout,
} from '../services/affiliate-wiring';
import { getPartnerStats } from '../services/affiliate-service';

export const affiliateHooks = new Hono<{ Bindings: Env }>();

// ── Internal webhook: signup referral ─────────────────────────────────────────

/**
 * POST /hooks/signup
 * Called internally when a tenant signs up with ?ref=CODE
 * No auth — internal webhook only
 * Body: { tenant_id: string, referral_code?: string }
 */
affiliateHooks.post('/hooks/signup', async (c) => {
  const body = await c.req.json().catch(() => ({})) as {
    tenant_id?: string;
    referral_code?: string;
  };

  if (!body.tenant_id) {
    return json({ error: 'tenant_id required', code: 'INVALID_INPUT' }, { status: 400 });
  }

  try {
    const partner = await processSignupReferral(c.env.DB, body.tenant_id, body.referral_code);
    return json({
      success: true,
      referred: !!partner,
      partner: partner ? { id: partner.id, code: partner.partner_code } : null,
    });
  } catch (err) {
    return json({ error: 'Referral processing failed', details: String(err) }, { status: 500 });
  }
});

// ── Internal webhook: payment commission ──────────────────────────────────────

/**
 * POST /hooks/payment
 * Called internally when Polar confirms payment
 * No auth — internal webhook only
 * Body: { tenant_id, amount, currency, transaction_id }
 */
affiliateHooks.post('/hooks/payment', async (c) => {
  const body = await c.req.json().catch(() => ({})) as {
    tenant_id?: string;
    amount?: number;
    currency?: string;
    transaction_id?: string;
  };

  if (!body.tenant_id || body.amount == null || !body.transaction_id) {
    return json(
      { error: 'tenant_id, amount, and transaction_id required', code: 'INVALID_INPUT' },
      { status: 400 }
    );
  }

  try {
    const commission = await processPaymentCommission(
      c.env.DB,
      body.tenant_id,
      body.amount,
      body.currency ?? 'USD',
      body.transaction_id
    );

    return json({
      success: true,
      commission_recorded: !!commission,
      commission: commission ?? null,
    });
  } catch (err) {
    return json({ error: 'Commission processing failed', details: String(err) }, { status: 500 });
  }
});

// ── Partner dashboard: earnings ───────────────────────────────────────────────

/**
 * GET /partner/earnings
 * Returns earnings summary for the authenticated partner
 */
affiliateHooks.get('/partner/earnings', auth(), async (c) => {
  const tenant = getTenant(c);

  const partner = await getPartnerStats(c.env.DB, tenant.tenantId);
  if (!partner) {
    return json({ error: 'Not registered as affiliate partner', code: 'NOT_FOUND' }, { status: 404 });
  }

  try {
    const earnings = await getPartnerEarnings(c.env.DB, partner.id);
    if (!earnings) {
      return json({ error: 'Failed to fetch earnings', code: 'NOT_FOUND' }, { status: 404 });
    }
    return json({ earnings });
  } catch (err) {
    return json({ error: 'Failed to fetch earnings', details: String(err) }, { status: 500 });
  }
});

// ── Partner dashboard: payout ─────────────────────────────────────────────────

/**
 * POST /partner/payout
 * Request payout for approved commissions
 * Body: { payout_method: 'polar' | 'bank' }
 */
affiliateHooks.post('/partner/payout', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as { payout_method?: string };

  const allowed = ['polar', 'bank'];
  if (!body.payout_method || !allowed.includes(body.payout_method)) {
    return json(
      { error: `payout_method must be one of: ${allowed.join(', ')}`, code: 'INVALID_INPUT' },
      { status: 400 }
    );
  }

  const partner = await getPartnerStats(c.env.DB, tenant.tenantId);
  if (!partner) {
    return json({ error: 'Not registered as affiliate partner', code: 'NOT_FOUND' }, { status: 404 });
  }

  try {
    const payout = await processCommissionPayout(c.env.DB, partner.id, body.payout_method);
    if (!payout) {
      return json({ error: 'No approved commissions available for payout', code: 'NO_BALANCE' }, { status: 422 });
    }
    return json({ success: true, payout });
  } catch (err) {
    return json({ error: 'Payout processing failed', details: String(err) }, { status: 500 });
  }
});
