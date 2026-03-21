/**
 * Credit management routes
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth } from '../middleware/auth';
import { rateLimit } from '../middleware/rate-limiter';
import { creditMetering } from '../middleware/credit-metering';
import { getTenant } from '../middleware/auth';
import { CreditService } from '../services/credit-service';
import { json } from '../utils/response';

export const credits = new Hono<{ Bindings: Env }>();

// All credit routes require auth
credits.use('/*', auth());
credits.use('/*', rateLimit());

/**
 * GET /v1/credits — Get current credit balance
 */
credits.get('/', (c) => {
  const tenant = getTenant(c);
  const creditService = new CreditService(c.env);

  return creditService.getAccount(tenant.tenantId).then((account) => {
    if (!account) {
      return json({ error: 'Account not found' }, { status: 404 });
    }

    return json({
      tenantId: account.tenantId,
      balance: account.balance,
      totalEarned: account.totalEarned,
      totalSpent: account.totalSpent,
    });
  });
});

/**
 * GET /v1/credits/history — Get transaction history
 */
credits.get('/history', (c) => {
  const tenant = getTenant(c);
  const creditService = new CreditService(c.env);

  const limit = Math.min(Math.max(parseInt(c.req.query('limit') || '50'), 1), 200);
  const offset = Math.max(0, parseInt(c.req.query('offset') || '0'), 0);

  return creditService.getHistory(tenant.tenantId, limit, offset).then((history) => {
    return json({
      tenantId: tenant.tenantId,
      history,
      pagination: { limit, offset },
    });
  });
});

/**
 * GET /v1/credits/usage — Get usage logs
 */
credits.get('/usage', (c) => {
  const tenant = getTenant(c);
  const creditService = new CreditService(c.env);

  const limit = Math.min(Math.max(parseInt(c.req.query('limit') || '50'), 1), 200);
  const missionId = c.req.query('mission_id');

  return creditService.getUsageLogs(tenant.tenantId, limit, missionId).then((logs) => {
    return json({
      tenantId: tenant.tenantId,
      logs,
      pagination: { limit },
    });
  });
});

/**
 * POST /v1/credits/check — Check credit cost for mission
 * Exempt from credit metering
 */
credits.post('/check', creditMetering({ cost: 0 }), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const complexity = body.complexity as 'simple' | 'standard' | 'complex' || 'standard';

  const creditService = new CreditService(c.env);
  const cost = creditService.getMissionCost(complexity);
  const balance = await creditService.getBalance(tenant.tenantId);

  return json({
    tenantId: tenant.tenantId,
    complexity,
    cost,
    balance,
    sufficient: balance >= cost,
  });
});

/**
 * POST /v1/credits/topup — Manual credit topup (admin only, for testing)
 * In production, this would be handled by Polar webhook
 */
credits.post('/topup', creditMetering({ cost: 0 }), async (c) => {
  const tenant = getTenant(c);

  // Admin-only endpoint
  if (!tenant.permissions.includes('admin')) {
    return json(
      { error: 'Admin permission required', code: 'FORBIDDEN' },
      { status: 403 }
    );
  }

  const body = await c.req.json().catch(() => ({}));
  const amount = parseInt(body.amount || '0', 10);
  const reason = body.reason || 'Manual topup';

  if (amount <= 0 || amount > 1000) {
    return json(
      { error: 'Amount must be between 1 and 1000', code: 'INVALID_AMOUNT' },
      { status: 400 }
    );
  }

  const creditService = new CreditService(c.env);
  const newBalance = await creditService.addCredits(
    tenant.tenantId,
    amount,
    'adjustment',
    reason,
    { source: 'manual_topup' }
  );

  return json({
    tenantId: tenant.tenantId,
    amountAdded: amount,
    newBalance,
    message: `Added ${amount} credits`,
  });
});

/**
 * POST /v1/credits/redeem — Redeem a promotional coupon code for bonus credits
 */
credits.post('/redeem', creditMetering({ cost: 0 }), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const code = body.code?.trim()?.toUpperCase();

  if (!code) {
    return json({ error: 'Coupon code required' }, { status: 400 });
  }

  // Find valid, active, non-expired coupon with remaining uses
  const coupon = await c.env.DB.prepare(
    `SELECT * FROM coupons WHERE code = ? AND active = 1 AND current_uses < max_uses
     AND (valid_until IS NULL OR valid_until >= datetime('now'))`
  ).bind(code).first<any>();

  if (!coupon) {
    return json({ error: 'Invalid or expired coupon', code: 'INVALID_COUPON' }, { status: 404 });
  }

  // Check if tenant already redeemed this coupon
  const existing = await c.env.DB.prepare(
    'SELECT id FROM coupon_redemptions WHERE coupon_id = ? AND tenant_id = ?'
  ).bind(coupon.id, tenant.tenantId).first();

  if (existing) {
    return json({ error: 'Coupon already redeemed', code: 'ALREADY_REDEEMED' }, { status: 409 });
  }

  // Apply bonus credits to tenant balance
  if (coupon.bonus_credits > 0) {
    await c.env.DB.prepare(
      'UPDATE tenants SET balance = balance + ?, total_earned = total_earned + ? WHERE id = ?'
    ).bind(coupon.bonus_credits, coupon.bonus_credits, tenant.tenantId).run();

    await c.env.DB.prepare(
      `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at)
       VALUES (?, ?, ?, 'adjustment', ?, ?, datetime('now'))`
    ).bind(
      crypto.randomUUID(),
      tenant.tenantId,
      coupon.bonus_credits,
      `Coupon: ${code}`,
      JSON.stringify({ coupon_id: coupon.id })
    ).run();
  }

  // Record redemption and increment usage counter
  await c.env.DB.prepare(
    'INSERT INTO coupon_redemptions (id, coupon_id, tenant_id) VALUES (?, ?, ?)'
  ).bind(crypto.randomUUID(), coupon.id, tenant.tenantId).run();

  await c.env.DB.prepare(
    'UPDATE coupons SET current_uses = current_uses + 1 WHERE id = ?'
  ).bind(coupon.id).run();

  return json({
    redeemed: true,
    code,
    bonusCredits: coupon.bonus_credits,
    message: `Coupon applied! ${coupon.bonus_credits} credits added.`,
  });
});

/**
 * POST /v1/credits/feedback — Submit feedback or churn survey response
 */
credits.post('/feedback', creditMetering({ cost: 0 }), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const type = body.type || 'general';
  const message = body.message?.trim();

  if (!message || message.length < 5) {
    return json({ error: 'Message required (min 5 chars)' }, { status: 400 });
  }

  const validTypes = ['churn', 'feature_request', 'bug', 'general'];
  if (!validTypes.includes(type)) {
    return json({ error: `Invalid type. Must be one of: ${validTypes.join(', ')}` }, { status: 400 });
  }

  await c.env.DB.prepare(
    `INSERT INTO tenant_feedback (id, tenant_id, type, message, previous_tier, created_at)
     VALUES (?, ?, ?, ?, ?, datetime('now'))`
  ).bind(
    crypto.randomUUID(),
    tenant.tenantId,
    type,
    message,
    body.previous_tier || null
  ).run();

  return json({ submitted: true, message: 'Thank you for your feedback!' });
});

/**
 * POST /v1/credits/purchase — Get Polar checkout URL for credit pack
 */
credits.post('/purchase', creditMetering({ cost: 0 }), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const pack = body.pack || 'credits-50';

  const packs: Record<string, { credits: number; price: number; name: string; polarId: string }> = {
    'credits-10':  { credits: 10,  price: 5,   name: '10 MCU Pack',  polarId: 'cd05c250-42dd-4333-a041-4f55b48044fb' },
    'credits-50':  { credits: 50,  price: 20,  name: '50 MCU Pack',  polarId: '5c0a8be0-b358-47ea-a006-681920f59676' },
    'credits-100': { credits: 100, price: 35,  name: '100 MCU Pack', polarId: 'c81ca25b-eb3a-43be-8224-de2578c64a94' },
    'credits-500': { credits: 500, price: 150, name: '500 MCU Pack', polarId: '9a6757bf-51da-40fc-80db-204a4aa0c61e' },
  };

  const selected = packs[pack];
  if (!selected) {
    return json(
      { error: 'Invalid pack. Options: credits-10, credits-50, credits-100, credits-500', code: 'INVALID_PACK' },
      { status: 400 }
    );
  }

  // Create dynamic Polar checkout session if API token available
  const polarToken = c.env.POLAR_API_TOKEN;
  if (polarToken) {
    try {
      const resp = await fetch('https://api.polar.sh/v1/checkouts/custom/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${polarToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: selected.polarId,
          payment_processor: 'stripe',
          success_url: 'https://app.agencyos.network/dashboard?payment=success',
          metadata: { tenant_id: tenant.tenantId, pack },
        }),
      });
      const checkout = await resp.json() as any;
      if (checkout?.url) {
        return json({ pack, credits: selected.credits, price: selected.price, currency: 'USD', checkoutUrl: checkout.url });
      }
    } catch { /* fallback below */ }
  }

  return json({
    pack,
    credits: selected.credits,
    price: selected.price,
    currency: 'USD',
    checkoutUrl: `https://landing.agencyos.network#pricing`,
    message: `Purchase ${selected.name} ($${selected.price}) — visit checkout to complete`,
  });
});
