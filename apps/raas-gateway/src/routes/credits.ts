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
 * POST /v1/credits/purchase — Get Polar checkout URL for credit pack
 */
credits.post('/purchase', creditMetering({ cost: 0 }), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const pack = body.pack || 'credits-50';

  const packs: Record<string, { credits: number; price: number; name: string }> = {
    'credits-10':  { credits: 10,  price: 5,   name: '10 MCU Pack' },
    'credits-50':  { credits: 50,  price: 20,  name: '50 MCU Pack' },
    'credits-100': { credits: 100, price: 35,  name: '100 MCU Pack' },
    'credits-500': { credits: 500, price: 150, name: '500 MCU Pack' },
  };

  const selected = packs[pack];
  if (!selected) {
    return json(
      { error: 'Invalid pack. Options: credits-10, credits-50, credits-100, credits-500', code: 'INVALID_PACK' },
      { status: 400 }
    );
  }

  // Return checkout info (tenant would use Polar checkout URL)
  return json({
    pack,
    credits: selected.credits,
    price: selected.price,
    currency: 'USD',
    checkoutUrl: `https://polar.sh/mekong-cli`,
    message: `Purchase ${selected.name} ($${selected.price}) — credits added automatically via webhook`,
  });
});
