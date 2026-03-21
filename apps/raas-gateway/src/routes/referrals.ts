/**
 * Referral system routes — generate codes, track stats, apply bonuses
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const referrals = new Hono<{ Bindings: Env }>();

const BONUS_CREDITS = 5;
const SIGNUP_BASE_URL = 'https://mekong-raas.pages.dev/signup';

/**
 * POST /v1/referrals/generate — Generate or return existing referral code
 */
referrals.post('/generate', auth(), async (c) => {
  const tenant = getTenant(c);

  const row = await c.env.DB.prepare(
    'SELECT referral_code FROM tenants WHERE id = ?'
  ).bind(tenant.tenantId).first<{ referral_code: string | null }>();

  if (row?.referral_code) {
    return json({
      referral_code: row.referral_code,
      referral_url: `${SIGNUP_BASE_URL}?ref=${row.referral_code}`,
    });
  }

  const code = crypto.randomUUID().slice(0, 8);

  await c.env.DB.prepare(
    'UPDATE tenants SET referral_code = ? WHERE id = ?'
  ).bind(code, tenant.tenantId).run();

  return json({
    referral_code: code,
    referral_url: `${SIGNUP_BASE_URL}?ref=${code}`,
  });
});

/**
 * GET /v1/referrals/stats — Get referral stats for authenticated tenant
 */
referrals.get('/stats', auth(), async (c) => {
  const tenant = getTenant(c);

  const [tenantRow, refs] = await Promise.all([
    c.env.DB.prepare(
      'SELECT referral_code, referral_count FROM tenants WHERE id = ?'
    ).bind(tenant.tenantId).first<{ referral_code: string | null; referral_count: number }>(),

    c.env.DB.prepare(
      'SELECT referred_id, bonus_credits, created_at FROM referrals WHERE referrer_id = ? ORDER BY created_at DESC'
    ).bind(tenant.tenantId).all<{ referred_id: string; bonus_credits: number; created_at: string }>(),
  ]);

  const refList = refs.results ?? [];
  const totalBonus = refList.reduce((sum, r) => sum + r.bonus_credits, 0);

  return json({
    referral_code: tenantRow?.referral_code ?? null,
    referral_count: tenantRow?.referral_count ?? 0,
    total_bonus_credits: totalBonus,
    referrals: refList,
  });
});

/**
 * POST /v1/referrals/apply — Apply a referral code (public, no auth)
 * Awards 5 bonus credits to both referrer and referred tenant
 */
referrals.post('/apply', async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const { referral_code, tenant_id } = body as { referral_code?: string; tenant_id?: string };

  if (!referral_code || !tenant_id) {
    return json({ error: 'referral_code and tenant_id are required', code: 'INVALID_INPUT' }, { status: 400 });
  }

  // Find referrer by code
  const referrer = await c.env.DB.prepare(
    'SELECT id FROM tenants WHERE referral_code = ?'
  ).bind(referral_code).first<{ id: string }>();

  if (!referrer) {
    return json({ error: 'Invalid referral code', code: 'INVALID_CODE' }, { status: 404 });
  }

  if (referrer.id === tenant_id) {
    return json({ error: 'Cannot refer yourself', code: 'SELF_REFERRAL' }, { status: 400 });
  }

  // Ensure referred tenant exists and hasn't been referred already
  const referred = await c.env.DB.prepare(
    'SELECT id, referred_by FROM tenants WHERE id = ?'
  ).bind(tenant_id).first<{ id: string; referred_by: string | null }>();

  if (!referred) {
    return json({ error: 'Tenant not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  if (referred.referred_by) {
    return json({ error: 'Tenant already has a referral applied', code: 'ALREADY_REFERRED' }, { status: 409 });
  }

  const refId = crypto.randomUUID();

  // Apply bonus credits to both parties and record referral atomically
  await Promise.all([
    c.env.DB.prepare(
      'UPDATE tenants SET balance = balance + ?, total_earned = total_earned + ?, referral_count = referral_count + 1 WHERE id = ?'
    ).bind(BONUS_CREDITS, BONUS_CREDITS, referrer.id).run(),

    c.env.DB.prepare(
      'UPDATE tenants SET balance = balance + ?, total_earned = total_earned + ?, referred_by = ? WHERE id = ?'
    ).bind(BONUS_CREDITS, BONUS_CREDITS, referral_code, tenant_id).run(),

    c.env.DB.prepare(
      `INSERT INTO referrals (id, referrer_id, referred_id, bonus_credits, status, created_at)
       VALUES (?, ?, ?, ?, 'completed', datetime('now'))`
    ).bind(refId, referrer.id, tenant_id, BONUS_CREDITS).run(),
  ]);

  return json({ success: true, bonus_credits: BONUS_CREDITS });
});
