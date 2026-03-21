/**
 * Tenant routes — signup, API key management, profile
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { AuthService } from '../services/auth-service';
import { EmailService } from '../services/email-service';
import { RateLimitService } from '../services/rate-limit-service';
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

  // Send welcome email — fire-and-forget, never blocks response
  const bonusCredits = refBy ? 15 : 10;
  const emailService = new EmailService(c.env);
  c.executionCtx.waitUntil(
    emailService.sendWelcome(email, name, referralCode, bonusCredits)
  );

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
 * POST /tenants/trial-extend — One-time trial extension: +10 bonus credits for social share
 * Idempotent: returns 409 if already claimed
 */
tenants.post('/trial-extend', async (c) => {
  const tenant = getTenant(c);

  // Guard: only one extension per tenant
  const existing = await c.env.DB.prepare(
    "SELECT id FROM credit_transactions WHERE tenant_id = ? AND description = 'Trial extension bonus'"
  ).bind(tenant.tenantId).first();

  if (existing) {
    return json({ error: 'Trial already extended', code: 'ALREADY_EXTENDED' }, { status: 409 });
  }

  // Credit 10 bonus MCU to tenant balance
  await c.env.DB.prepare(
    'UPDATE tenants SET balance = balance + 10, total_earned = total_earned + 10 WHERE id = ?'
  ).bind(tenant.tenantId).run();

  await c.env.DB.prepare(
    `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at)
     VALUES (?, ?, 10, 'adjustment', 'Trial extension bonus', '{"source":"social_share"}', datetime('now'))`
  ).bind(crypto.randomUUID(), tenant.tenantId).run();

  return json({ credited: 10, message: 'Thank you for sharing! 10 bonus credits added.' });
});

/**
 * GET /tenants/limits — Show current rate limits and usage quotas for this tenant
 */
tenants.get('/limits', async (c) => {
  const tenant = getTenant(c);
  const rateLimitService = new RateLimitService(c.env);

  const [rateLimits, quota] = await Promise.all([
    Promise.resolve(rateLimitService.getTierLimits(tenant.tier)),
    rateLimitService.checkMonthlyQuota(tenant.tenantId, tenant.tier),
  ]);

  const percentUsed = quota.limit === -1
    ? 0
    : Math.round((quota.used / quota.limit) * 100);

  return json({
    tier: tenant.tier,
    rateLimits: {
      requestsPerMinute: rateLimits.requestsPerMinute,
      monthlyMissions: rateLimits.monthlyMissions,
    },
    usage: {
      missionsThisMonth: quota.used,
      remaining: quota.remaining,
      percentUsed,
    },
  });
});

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
 * GET /tenants/upgrade — Compare current tier vs available upgrades
 */
tenants.get('/upgrade', async (c) => {
  const tenant = getTenant(c);

  const polarProductIds: Record<string, string> = {
    starter: 'ce215739-4684-4deb-b257-8321ea4d844d',
    pro: 'b810b7eb-97f9-4ed0-9c26-07f4bfbbf58f',
    agency: '0e752654-5cb6-4f48-a990-b2d3eb6a2429',
    master: 'dc82a4bb-ad5d-473c-ac29-67b6397700ec',
  };

  const tiers = [
    { id: 'free', name: 'Free', price: 0, credits: 10, dailyLimit: 3, features: ['Community support'] },
    { id: 'starter', name: 'Starter', price: 29, credits: 50, dailyLimit: 15, features: ['Email support', 'All 5 layers'] },
    { id: 'pro', name: 'Pro', price: 99, credits: 200, dailyLimit: 50, features: ['Priority support', 'Analytics', 'Premium models', 'Batch missions'] },
    { id: 'agency', name: 'Agency', price: 199, credits: 500, dailyLimit: -1, features: ['Dedicated support', 'Unlimited missions', 'Webhook callbacks'] },
    { id: 'master', name: 'Master', price: 399, credits: 1000, dailyLimit: -1, features: ['SSO', 'Audit logs', 'Custom integrations', 'Priority queue'] },
  ];

  const currentIdx = tiers.findIndex(t => t.id === tenant.tier);
  const current = tiers[currentIdx] || tiers[0];
  const upgrades = tiers.slice(Math.max(currentIdx + 1, 1));

  // Generate dynamic Polar checkout URLs for upgrades
  const polarToken = c.env.POLAR_API_TOKEN;
  if (polarToken) {
    for (const tier of upgrades) {
      const productId = polarProductIds[tier.id];
      if (productId) {
        try {
          const resp = await fetch('https://api.polar.sh/v1/checkouts/custom/', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${polarToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, payment_processor: 'stripe', success_url: 'https://app.agencyos.network/dashboard?payment=success', metadata: { tenant_id: tenant.tenantId } }),
          });
          const checkout = await resp.json() as any;
          if (checkout?.url) (tier as any).checkoutUrl = checkout.url;
        } catch { /* fallback: no checkout URL */ }
      }
    }
  }

  return json({ currentTier: current, upgrades });
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
 * GET /tenants/usage — Monthly usage summary for current billing period
 */
tenants.get('/usage', async (c) => {
  const tenant = getTenant(c);
  const tid = tenant.tenantId;

  const [monthly, daily, byComplexity, byProject] = await Promise.all([
    // This month's totals
    c.env.DB.prepare(
      `SELECT COUNT(*) as totalMissions,
              SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
              SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
              COALESCE(SUM(credits_cost), 0) as totalCredits
       FROM missions WHERE tenant_id = ?
       AND created_at >= datetime('now', 'start of month')`
    ).bind(tid).first(),

    // Daily breakdown (last 30 days)
    c.env.DB.prepare(
      `SELECT date(created_at) as day, COUNT(*) as missions, SUM(credits_cost) as credits
       FROM missions WHERE tenant_id = ? AND created_at >= datetime('now', '-30 days')
       GROUP BY date(created_at) ORDER BY day DESC`
    ).bind(tid).all(),

    // By complexity
    c.env.DB.prepare(
      `SELECT complexity, COUNT(*) as count, SUM(credits_cost) as credits
       FROM missions WHERE tenant_id = ? AND created_at >= datetime('now', 'start of month')
       GROUP BY complexity`
    ).bind(tid).all(),

    // By project
    c.env.DB.prepare(
      `SELECT COALESCE(project, 'default') as project, COUNT(*) as missions, SUM(credits_cost) as credits
       FROM missions WHERE tenant_id = ? AND created_at >= datetime('now', 'start of month')
       GROUP BY project ORDER BY credits DESC LIMIT 10`
    ).bind(tid).all(),
  ]);

  return json({
    period: 'current_month',
    summary: monthly || { totalMissions: 0, completed: 0, failed: 0, totalCredits: 0 },
    daily: daily.results,
    byComplexity: byComplexity.results,
    byProject: byProject.results,
  });
});

/**
 * GET /tenants/invoices — Transaction history for billing
 */
tenants.get('/invoices', async (c) => {
  const tenant = getTenant(c);
  const limit = Math.min(parseInt(c.req.query('limit') || '50'), 100);
  const offset = parseInt(c.req.query('offset') || '0');
  const type = c.req.query('type'); // filter: purchase, adjustment, refund, deduction
  const from = c.req.query('from'); // ISO date
  const to = c.req.query('to'); // ISO date

  let query = 'SELECT * FROM credit_transactions WHERE tenant_id = ?';
  const bindings: any[] = [tenant.tenantId];

  if (type) { query += ' AND type = ?'; bindings.push(type); }
  if (from) { query += ' AND created_at >= ?'; bindings.push(from); }
  if (to) { query += ' AND created_at <= ?'; bindings.push(to); }

  // Get total count
  const countQuery = query.replace('SELECT *', 'SELECT COUNT(*) as total');
  const total = await c.env.DB.prepare(countQuery).bind(...bindings).first<{total: number}>();

  query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
  bindings.push(limit, offset);

  const transactions = await c.env.DB.prepare(query).bind(...bindings).all();

  // Summary
  const summary = await c.env.DB.prepare(
    `SELECT type, COUNT(*) as count, COALESCE(SUM(amount),0) as total_amount
     FROM credit_transactions WHERE tenant_id = ?
     GROUP BY type`
  ).bind(tenant.tenantId).all();

  return json({
    transactions: transactions.results,
    total: total?.total ?? 0,
    pagination: { limit, offset },
    summary: summary.results,
  });
});

/**
 * PUT /tenants/settings — Update tenant notification and webhook settings
 * Accepts: webhook_url (must be https://), notify_email, notify_telegram
 */
tenants.put('/settings', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));
  const webhookUrl = body.webhook_url?.trim() || null;
  const notifyEmail = body.notify_email !== false;
  const notifyTelegram = body.notify_telegram !== false;

  // Validate webhook_url must be https:// if provided
  if (webhookUrl !== null) {
    try {
      const parsed = new URL(webhookUrl);
      if (parsed.protocol !== 'https:') {
        return json({ error: 'webhook_url must use https://', code: 'INVALID_WEBHOOK_URL' }, { status: 400 });
      }
    } catch {
      return json({ error: 'webhook_url is not a valid URL', code: 'INVALID_WEBHOOK_URL' }, { status: 400 });
    }
  }

  await c.env.DB.prepare(
    `UPDATE tenants SET webhook_url = ?, notify_email = ?, notify_telegram = ?, updated_at = datetime('now') WHERE id = ?`
  ).bind(webhookUrl, notifyEmail ? 1 : 0, notifyTelegram ? 1 : 0, tenant.tenantId).run();

  return json({ updated: true, webhookUrl, notifyEmail, notifyTelegram });
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
