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
 * POST /billing/webhook — Polar.sh webhook endpoint
 *
 * Events handled:
 * - order.paid: Allocate credits, update tier
 * - subscription.active: Activate subscription, update tier
 * - subscription.canceled: Downgrade to starter
 * - refund.created: Deduct credits
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

  // Get webhook signature
  const signature = c.req.header('webhook-signature') || '';
  const rawBody = await c.req.text();

  // Verify signature
  const validSignature = await billingService.verifySignature(rawBody, signature);
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
