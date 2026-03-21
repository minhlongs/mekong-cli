/**
 * Billing routes — Polar.sh webhook integration
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { BillingService, PolarEvent } from '../services/billing-service';
import { authRateLimit } from '../middleware/auth-rate-limit';
import { json } from '../utils/response';

export const billing = new Hono<{ Bindings: Env }>();

/**
 * Tier-to-credits mapping — match by first 8 chars of product_id
 */
const TIER_CREDITS: Record<string, { tier: string; credits: number }> = {
  'ce215739': { tier: 'starter', credits: 50 },
  'b810b7eb': { tier: 'pro', credits: 200 },
  '0e752654': { tier: 'agency', credits: 500 },
  'dc82a4bb': { tier: 'master', credits: 1000 },
};

/**
 * Resolve tier config from product_id (first 8 chars)
 */
function resolveTierFromProductId(productId: string): { tier: string; credits: number } | null {
  const prefix = productId.slice(0, 8);
  return TIER_CREDITS[prefix] || null;
}

/**
 * POST /billing/webhook — Polar.sh webhook endpoint
 *
 * Events handled:
 * - order.paid: Allocate credits, update tier
 * - subscription.active: Activate subscription, update tier
 * - subscription.canceled: Downgrade to starter
 * - refund.created: Deduct credits
 * - subscription.created: Create subscription record, upgrade tier, add monthly credits
 * - subscription.updated: Update period dates, reload monthly credits
 * - subscription.cancelled: Mark cancelled, schedule tier downgrade at period end
 * - subscription.revoked: Immediately downgrade to free tier, mark expired
 */
billing.post('/webhook', authRateLimit(), async (c) => {
  const billingService = new BillingService(c.env);

  // Check D1 configured
  if (!c.env.DB) {
    return json(
      { error: 'Database not configured', code: 'SERVICE_UNAVAILABLE' },
      { status: 503 }
    );
  }

  // Get Standard Webhooks headers
  const signature = c.req.header('webhook-signature') || '';
  const webhookId = c.req.header('webhook-id') || '';
  const webhookTimestamp = c.req.header('webhook-timestamp') || '';
  const rawBody = await c.req.text();

  // Verify signature (Standard Webhooks format)
  const validSignature = await billingService.verifySignature(
    rawBody, signature, webhookId, webhookTimestamp
  );
  if (!validSignature) {
    return json(
      { error: 'Invalid webhook signature', code: 'INVALID_SIGNATURE' },
      { status: 401 }
    );
  }

  // Parse event
  let event: PolarEvent;
  try {
    event = JSON.parse(rawBody);
  } catch (error) {
    return json(
      { error: 'Invalid JSON payload', code: 'INVALID_JSON' },
      { status: 400 }
    );
  }

  // Validate timestamp (prevent replay attacks)
  const timestamp = event.timestamp || event.created_at;
  if (timestamp && !billingService.isValidTimestamp(timestamp)) {
    return json(
      {
        error: 'Webhook timestamp too old (replay attack prevented)',
        code: 'REPLAY_ATTACK',
      },
      { status: 401 }
    );
  }

  // Check for duplicate event (idempotency)
  if (event.id) {
    const isDuplicate = await billingService.isDuplicateEvent(event.id);
    if (isDuplicate) {
      return json(
        { error: 'Duplicate event detected', code: 'REPLAY_ATTACK' },
        { status: 409 }
      );
    }
  }

  // Process event by type
  let result: { success: boolean; credits?: number; tier?: string; deducted?: number } = {
    success: false,
  };

  try {
    switch (event.type) {
      case 'order.paid':
        result = await billingService.processOrderPaid(event);
        break;

      case 'subscription.active':
        result = await billingService.processSubscriptionActive(event);
        break;

      case 'subscription.canceled':
        result = await billingService.processSubscriptionCanceled(event);
        break;

      case 'refund.created':
        result = await billingService.processRefund(event);
        break;

      case 'subscription.created':
        result = await handleSubscriptionCreated(c.env, event);
        break;

      case 'subscription.updated':
        result = await handleSubscriptionUpdated(c.env, event);
        break;

      case 'subscription.cancelled':
        result = await handleSubscriptionCancelled(c.env, event);
        break;

      case 'subscription.revoked':
        result = await handleSubscriptionRevoked(c.env, event);
        break;

      default:
        // Unknown event type - still acknowledge
        console.log('[BillingService] Unknown event type:', event.type);
        return json({ received: true, event: event.type });
    }

    // Record event if we have an ID
    if (event.id) {
      await billingService.recordEvent(event.id, event.type, result.success);
    }

    // Return result
    if (result.success) {
      const response: any = { received: true, event: event.type };
      if (result.credits) response.credits = result.credits;
      if (result.tier) response.tier = result.tier;
      if (result.deducted) response.deducted = result.deducted;
      return json(response);
    } else {
      return json(
        {
          received: true,
          event: event.type,
          warning: 'Event processed but no action taken',
        },
        { status: 200 }
      );
    }
  } catch (error) {
    console.error('[BillingService] Error processing event:', error);

    // Record failed event
    if (event.id) {
      await billingService.recordEvent(event.id, event.type, false);
    }

    return json(
      { error: 'Internal server error', code: 'WEBHOOK_PROCESSING_ERROR' },
      { status: 500 }
    );
  }
});

// ---------------------------------------------------------------------------
// Subscription lifecycle handlers
// ---------------------------------------------------------------------------

/**
 * subscription.created — create DB record, upgrade tier, add monthly credits
 */
async function handleSubscriptionCreated(
  env: Env,
  event: PolarEvent
): Promise<{ success: boolean; credits?: number; tier?: string }> {
  const sub = (event.data as any).subscription;
  const customer = (event.data as any).customer;

  const tenantId = customer?.external_id || (event.data as any).metadata?.tenant_id;
  if (!tenantId || !sub) {
    console.error('[Billing] subscription.created: missing tenantId or subscription data');
    return { success: false };
  }

  const tierConfig = resolveTierFromProductId(sub.product_id || '');
  if (!tierConfig) {
    console.warn('[Billing] subscription.created: unknown product_id', sub.product_id);
    return { success: false };
  }

  const now = new Date().toISOString();

  // Upsert subscription record
  await env.DB.prepare(
    `INSERT INTO subscriptions
       (id, tenant_id, polar_subscription_id, tier, status,
        current_period_start, current_period_end, credits_per_period, created_at, updated_at)
     VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
     ON CONFLICT(polar_subscription_id) DO UPDATE SET
       status = 'active',
       current_period_start = excluded.current_period_start,
       current_period_end = excluded.current_period_end,
       updated_at = excluded.updated_at`
  )
    .bind(
      crypto.randomUUID(),
      tenantId,
      sub.id,
      tierConfig.tier,
      sub.current_period_start || now,
      sub.current_period_end || now,
      tierConfig.credits,
      now,
      now
    )
    .run();

  // Upgrade tenant tier
  await env.DB.prepare(
    "UPDATE tenants SET tier = ?, updated_at = datetime('now') WHERE id = ?"
  )
    .bind(tierConfig.tier, tenantId)
    .run();

  // Add monthly credits via CreditService
  const { CreditService } = await import('../services/credit-service');
  const creditService = new CreditService(env);
  await creditService.addCredits(
    tenantId,
    tierConfig.credits,
    'purchase',
    `Subscription started: ${tierConfig.tier}`,
    { subscription_id: sub.id, event_id: event.id }
  );

  console.log(`[Billing] subscription.created: ${tenantId} → ${tierConfig.tier} +${tierConfig.credits} credits`);
  return { success: true, tier: tierConfig.tier, credits: tierConfig.credits };
}

/**
 * subscription.updated — update period dates, reload monthly credits (renewal)
 */
async function handleSubscriptionUpdated(
  env: Env,
  event: PolarEvent
): Promise<{ success: boolean; credits?: number; tier?: string }> {
  const sub = (event.data as any).subscription;
  const customer = (event.data as any).customer;

  const tenantId = customer?.external_id || (event.data as any).metadata?.tenant_id;
  if (!tenantId || !sub) {
    console.error('[Billing] subscription.updated: missing tenantId or subscription data');
    return { success: false };
  }

  const now = new Date().toISOString();

  // Fetch existing subscription to get credits_per_period
  const existing = await env.DB.prepare(
    'SELECT credits_per_period, tier FROM subscriptions WHERE polar_subscription_id = ?'
  )
    .bind(sub.id)
    .first<{ credits_per_period: number; tier: string }>();

  // Update period dates in DB
  await env.DB.prepare(
    `UPDATE subscriptions SET
       current_period_start = ?,
       current_period_end = ?,
       status = 'active',
       updated_at = ?
     WHERE polar_subscription_id = ?`
  )
    .bind(
      sub.current_period_start || now,
      sub.current_period_end || now,
      now,
      sub.id
    )
    .run();

  // Reload monthly credits if subscription found
  const creditsToAdd = existing?.credits_per_period ?? 0;
  const tier = existing?.tier ?? '';

  if (creditsToAdd > 0) {
    const { CreditService } = await import('../services/credit-service');
    const creditService = new CreditService(env);
    await creditService.addCredits(
      tenantId,
      creditsToAdd,
      'rollover',
      `Subscription renewal: ${tier}`,
      { subscription_id: sub.id, event_id: event.id }
    );
    console.log(`[Billing] subscription.updated: ${tenantId} renewed +${creditsToAdd} credits`);
    return { success: true, credits: creditsToAdd, tier };
  }

  console.log(`[Billing] subscription.updated: ${tenantId} period dates refreshed (no credits reloaded)`);
  return { success: true };
}

/**
 * subscription.cancelled — mark cancelled, keep tier until period end
 */
async function handleSubscriptionCancelled(
  env: Env,
  event: PolarEvent
): Promise<{ success: boolean }> {
  const sub = (event.data as any).subscription;
  const customer = (event.data as any).customer;

  const tenantId = customer?.external_id || (event.data as any).metadata?.tenant_id;
  if (!tenantId || !sub) {
    console.error('[Billing] subscription.cancelled: missing tenantId or subscription data');
    return { success: false };
  }

  // Mark as cancelled — tier stays until current_period_end (Polar handles expiry via revoked)
  await env.DB.prepare(
    "UPDATE subscriptions SET status = 'cancelled', updated_at = datetime('now') WHERE polar_subscription_id = ?"
  )
    .bind(sub.id)
    .run();

  console.log(`[Billing] subscription.cancelled: ${tenantId} marked cancelled, tier active until period end`);
  return { success: true };
}

/**
 * subscription.revoked — immediately downgrade to free tier, mark expired
 */
async function handleSubscriptionRevoked(
  env: Env,
  event: PolarEvent
): Promise<{ success: boolean; tier?: string }> {
  const sub = (event.data as any).subscription;
  const customer = (event.data as any).customer;

  const tenantId = customer?.external_id || (event.data as any).metadata?.tenant_id;
  if (!tenantId || !sub) {
    console.error('[Billing] subscription.revoked: missing tenantId or subscription data');
    return { success: false };
  }

  // Mark subscription as expired
  await env.DB.prepare(
    "UPDATE subscriptions SET status = 'expired', updated_at = datetime('now') WHERE polar_subscription_id = ?"
  )
    .bind(sub.id)
    .run();

  // Immediately downgrade tenant to free tier
  await env.DB.prepare(
    "UPDATE tenants SET tier = 'free', updated_at = datetime('now') WHERE id = ?"
  )
    .bind(tenantId)
    .run();

  console.log(`[Billing] subscription.revoked: ${tenantId} downgraded to free immediately`);
  return { success: true, tier: 'free' };
}

/**
 * GET /billing/webhook/status — Check webhook service status
 */
billing.get('/webhook/status', (c) => {
  return json({
    status: 'healthy',
    configured: !!c.env.POLAR_WEBHOOK_SECRET,
    timestamp: new Date().toISOString(),
  });
});

/**
 * GET /billing/pricing — Public pricing information
 */
billing.get('/pricing', (c) => {
  return json({
    tiers: [
      { id: 'free', name: 'Free', price: 0, credits: 10, description: 'Try it out' },
      { id: 'agencyos-starter', name: 'Starter', price: 29, credits: 50, description: 'Solo non-tech user' },
      { id: 'agencyos-pro', name: 'Pro', price: 99, credits: 200, description: 'Small agency' },
      { id: 'agencyos-agency', name: 'Agency', price: 199, credits: 500, description: 'Growing agency' },
      { id: 'agencyos-master', name: 'Master', price: 399, credits: 1000, description: 'Premium agency' },
    ],
    credit_packs: [
      { id: 'credits-10', credits: 10, price: 5 },
      { id: 'credits-50', credits: 50, price: 20 },
      { id: 'credits-100', credits: 100, price: 35 },
      { id: 'credits-500', credits: 500, price: 150 },
    ],
    credit_costs: {
      simple: 1,
      standard: 3,
      complex: 5,
    },
  });
});
