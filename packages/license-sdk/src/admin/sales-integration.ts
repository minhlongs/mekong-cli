import type { LicenseTier } from '../core/tiers.js';
import { generateKey } from '../core/key-generator.js';

// --- Event types ---

export interface StripeEvent {
  type: string;
  customer: string;
  amount: number;
  metadata?: Record<string, string>;
}

export interface PaddleEvent {
  event_type: string;
  subscription_id: string;
  plan: string;
}

export interface PolarEvent {
  type: string;
  subscription: {
    id: string;
    product?: { name?: string };
    tier?: string;
  };
}

export interface WebhookResult {
  success: boolean;
  key?: string;
  error?: string;
}

// --- Tier mapping helpers ---

const STRIPE_AMOUNT_TIER: Array<{ maxCents: number; tier: LicenseTier }> = [
  { maxCents: 4999, tier: 'starter' },
  { maxCents: 14999, tier: 'pro' },
  { maxCents: 49999, tier: 'enterprise' },
];

function tierFromStripeAmount(amountCents: number): LicenseTier {
  for (const entry of STRIPE_AMOUNT_TIER) {
    if (amountCents <= entry.maxCents) return entry.tier;
  }
  return 'enterprise';
}

function tierFromPaddlePlan(plan: string): LicenseTier {
  const lower = plan.toLowerCase();
  if (lower.includes('enterprise')) return 'enterprise';
  if (lower.includes('pro')) return 'pro';
  return 'starter';
}

function tierFromPolarProduct(name: string | undefined, raw: string | undefined): LicenseTier {
  const src = (name ?? raw ?? '').toLowerCase();
  if (src.includes('enterprise')) return 'enterprise';
  if (src.includes('pro')) return 'pro';
  return 'starter';
}

// --- Handler class ---

/**
 * Handles inbound webhooks from Stripe, Paddle, and Polar.
 * Generates a license key on successful payment/subscription events.
 */
export class SalesWebhookHandler {
  private readonly brand: string;

  constructor(brand: string) {
    this.brand = brand;
  }

  /** Stripe: payment_intent.succeeded → generate key */
  handleStripeWebhook(payload: StripeEvent): WebhookResult {
    if (payload.type !== 'payment_intent.succeeded') {
      return { success: false, error: `Unhandled Stripe event type: ${payload.type}` };
    }

    try {
      const tier = tierFromStripeAmount(payload.amount);
      const owner = payload.customer;
      const record = generateKey(this.brand as any, tier, owner);
      return { success: true, key: record.key };
    } catch (err) {
      return { success: false, error: String(err) };
    }
  }

  /** Paddle: subscription.created → generate key */
  handlePaddleWebhook(payload: PaddleEvent): WebhookResult {
    if (payload.event_type !== 'subscription.created') {
      return { success: false, error: `Unhandled Paddle event type: ${payload.event_type}` };
    }

    try {
      const tier = tierFromPaddlePlan(payload.plan);
      const owner = payload.subscription_id;
      const record = generateKey(this.brand as any, tier, owner);
      return { success: true, key: record.key };
    } catch (err) {
      return { success: false, error: String(err) };
    }
  }

  /** Polar: subscription.created → generate key */
  handlePolarWebhook(payload: PolarEvent): WebhookResult {
    if (payload.type !== 'subscription.created') {
      return { success: false, error: `Unhandled Polar event type: ${payload.type}` };
    }

    try {
      const tier = tierFromPolarProduct(
        payload.subscription.product?.name,
        payload.subscription.tier
      );
      const owner = payload.subscription.id;
      const record = generateKey(this.brand as any, tier, owner);
      return { success: true, key: record.key };
    } catch (err) {
      return { success: false, error: String(err) };
    }
  }
}
