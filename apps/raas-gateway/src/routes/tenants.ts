/**
 * Tenant routes — signup, API key management, profile
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { AuthService } from '../services/auth-service';
import { json } from '../utils/response';

export const tenants = new Hono<{ Bindings: Env }>();

/**
 * POST /tenants/signup — Create a new tenant (public, no auth)
 * Returns JWT token for immediate use
 */
tenants.post('/signup', async (c) => {
  const body = await c.req.json().catch(() => ({}));

  const name = body.name?.trim();
  const email = body.email?.trim()?.toLowerCase();

  if (!name || name.length < 2) {
    return json({ error: 'Name required (min 2 chars)', code: 'INVALID_NAME' }, { status: 400 });
  }

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return json({ error: 'Valid email required', code: 'INVALID_EMAIL' }, { status: 400 });
  }

  // Check duplicate email
  const existing = await c.env.DB.prepare('SELECT id FROM tenants WHERE email = ?')
    .bind(email)
    .first<{ id: string }>();

  if (existing) {
    return json({ error: 'Email already registered', code: 'EMAIL_EXISTS' }, { status: 409 });
  }

  // Create tenant with free tier + 10 starter credits + referral code
  const tenantId = crypto.randomUUID();
  const referralCode = tenantId.slice(0, 8);
  const refBy = body.ref?.trim() || null;

  await c.env.DB.prepare(
    `INSERT INTO tenants (id, name, email, tier, active, balance, total_earned, total_spent, referral_code, referred_by, created_at, updated_at)
     VALUES (?, ?, ?, 'free', 1, 10, 10, 0, ?, ?, datetime('now'), datetime('now'))`
  )
    .bind(tenantId, name, email, referralCode, refBy)
    .run();

  // Record initial credits transaction
  await c.env.DB.prepare(
    `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at)
     VALUES (?, ?, 10, 'adjustment', 'Welcome bonus', '{}', datetime('now'))`
  )
    .bind(crypto.randomUUID(), tenantId)
    .run();

  // Process referral: +5 MCU to both referrer and new user
  if (refBy) {
    const referrer = await c.env.DB.prepare(
      'SELECT id FROM tenants WHERE referral_code = ?'
    ).bind(refBy).first<{ id: string }>();

    if (referrer) {
      // Bonus to new user
      await c.env.DB.prepare('UPDATE tenants SET balance = balance + 5, total_earned = total_earned + 5 WHERE id = ?')
        .bind(tenantId).run();
      await c.env.DB.prepare(
        `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at) VALUES (?, ?, 5, 'adjustment', 'Referral bonus', '{}', datetime('now'))`
      ).bind(crypto.randomUUID(), tenantId).run();

      // Bonus to referrer
      await c.env.DB.prepare('UPDATE tenants SET balance = balance + 5, total_earned = total_earned + 5 WHERE id = ?')
        .bind(referrer.id).run();
      await c.env.DB.prepare(
        `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at) VALUES (?, ?, 5, 'adjustment', 'Referral reward', '{}', datetime('now'))`
      ).bind(crypto.randomUUID(), referrer.id).run();
    }
  }

  // Generate JWT
  const authService = new AuthService(c.env);
  const token = await authService.generateJwt(tenantId, 'free', ['read', 'write']);

  const bonusCredits = refBy ? 15 : 10;
  return json({
    tenantId,
    name,
    email,
    tier: 'free',
    credits: bonusCredits,
    referralCode,
    token,
    message: refBy
      ? 'Welcome! You have 15 credits (10 + 5 referral bonus).'
      : `Welcome! You have 10 free credits. Share your referral code: ${referralCode}`,
  }, { status: 201 });
});

/**
 * POST /tenants/login — Get new JWT for existing account (public)
 */
tenants.post('/login', async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const email = body.email?.trim()?.toLowerCase();

  if (!email) {
    return json({ error: 'Email required', code: 'INVALID_EMAIL' }, { status: 400 });
  }

  const tenant = await c.env.DB.prepare(
    'SELECT id, name, tier, active FROM tenants WHERE email = ?'
  ).bind(email).first<{ id: string; name: string; tier: string; active: number }>();

  if (!tenant || !tenant.active) {
    return json({ error: 'Account not found or inactive', code: 'NOT_FOUND' }, { status: 404 });
  }

  const authService = new AuthService(c.env);
  const token = await authService.generateJwt(tenant.id, tenant.tier, ['read', 'write']);

  return json({ tenantId: tenant.id, name: tenant.name, tier: tenant.tier, token });
});

// All routes below require auth
tenants.use('/*', auth());

/**
 * GET /tenants/profile — Get current tenant profile
 */
tenants.get('/profile', async (c) => {
  const tenant = getTenant(c);

  const profile = await c.env.DB.prepare(
    `SELECT id, name, email, tier, active, balance, total_earned, total_spent, created_at
     FROM tenants WHERE id = ?`
  )
    .bind(tenant.tenantId)
    .first();

  if (!profile) {
    return json({ error: 'Tenant not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  return json(profile);
});

/**
 * GET /tenants/referrals — View referral stats
 */
tenants.get('/referrals', async (c) => {
  const tenant = getTenant(c);

  const profile = await c.env.DB.prepare(
    'SELECT referral_code FROM tenants WHERE id = ?'
  ).bind(tenant.tenantId).first<{ referral_code: string }>();

  const referred = await c.env.DB.prepare(
    'SELECT COUNT(*) as count FROM tenants WHERE referred_by = ?'
  ).bind(profile?.referral_code || '').first<{ count: number }>();

  const creditsEarned = (referred?.count ?? 0) * 5;

  return json({
    referralCode: profile?.referral_code || null,
    referralLink: `https://mekong-raas.pages.dev?ref=${profile?.referral_code || ''}`,
    totalReferred: referred?.count ?? 0,
    creditsEarned,
    rewardPerReferral: 5,
  });
});

/**
 * POST /tenants/api-keys — Generate a new API key
 */
tenants.post('/api-keys', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const name = body.name?.trim() || 'Default Key';

  const authService = new AuthService(c.env);
  const { apiKey, keyId } = await authService.createApiKey(
    tenant.tenantId, name, tenant.permissions
  );

  return json({
    keyId,
    apiKey, // Only shown once — cannot be retrieved later
    name,
    message: 'Save this API key — it cannot be retrieved again.',
  }, { status: 201 });
});

/**
 * GET /tenants/api-keys — List API keys (without secrets)
 */
tenants.get('/api-keys', async (c) => {
  const tenant = getTenant(c);
  const authService = new AuthService(c.env);
  const keys = await authService.getApiKeys(tenant.tenantId);

  return json({ keys });
});

/**
 * GET /tenants/digest — Weekly usage summary for email integration
 */
tenants.get('/digest', async (c) => {
  const tenant = getTenant(c);
  const tid = tenant.tenantId;

  const [missions, credits, topGoals] = await Promise.all([
    c.env.DB.prepare(
      `SELECT COUNT(*) as total,
              SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
              SUM(credits_cost) as cost
       FROM missions WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')`
    ).bind(tid).first<{ total: number; completed: number; cost: number }>(),
    c.env.DB.prepare('SELECT balance FROM tenants WHERE id = ?').bind(tid).first<{ balance: number }>(),
    c.env.DB.prepare(
      `SELECT goal, status, credits_cost FROM missions
       WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')
       ORDER BY created_at DESC LIMIT 5`
    ).bind(tid).all<{ goal: string; status: string; credits_cost: number }>(),
  ]);

  return json({
    period: 'last_7_days',
    missions: { total: missions?.total ?? 0, completed: missions?.completed ?? 0, creditsUsed: missions?.cost ?? 0 },
    balance: credits?.balance ?? 0,
    recentGoals: topGoals.results.map(g => ({ goal: g.goal.slice(0, 80), status: g.status, cost: g.credits_cost })),
  });
});

/**
 * DELETE /tenants/api-keys/:id — Revoke an API key
 */
tenants.delete('/api-keys/:id', async (c) => {
  const tenant = getTenant(c);
  const keyId = c.req.param('id');

  const authService = new AuthService(c.env);
  const revoked = await authService.revokeApiKey(keyId, tenant.tenantId);

  if (!revoked) {
    return json({ error: 'Key not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  return json({ revoked: true, keyId });
});
