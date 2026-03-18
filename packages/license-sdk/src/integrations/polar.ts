import { createHmac } from 'node:crypto';
import { generateKey } from '../core/key-generator.js';
import type { Brand, LicenseTier } from '../core/tiers.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PolarWebhookEvent {
  type: string;
  data: {
    product_id: string;
    customer_email: string;
    subscription_id?: string;
  };
}

export interface WebhookResult {
  success: boolean;
  action: 'key_issued' | 'subscription_cancelled' | 'ignored' | 'error';
  key?: string;
  brand?: Brand;
  tier?: LicenseTier;
  error?: string;
}

interface ProductConfig {
  brand: Brand;
  tier: LicenseTier;
  price: number;
}

// ---------------------------------------------------------------------------
// Product map — 18 products across 6 brands
// ---------------------------------------------------------------------------

export const POLAR_PRODUCTS: Record<string, ProductConfig> = {
  'mekong-starter':    { brand: 'MEKONG',    tier: 'starter',    price: 29 },
  'mekong-pro':        { brand: 'MEKONG',    tier: 'pro',        price: 99 },
  'mekong-enterprise': { brand: 'MEKONG',    tier: 'enterprise', price: 299 },
  'sophia-creator':    { brand: 'SOPHIA',    tier: 'starter',    price: 19 },
  'sophia-pro':        { brand: 'SOPHIA',    tier: 'pro',        price: 49 },
  'sophia-agency':     { brand: 'SOPHIA',    tier: 'enterprise', price: 149 },
  'well-growth':       { brand: 'WELL',      tier: 'starter',    price: 29 },
  'well-pro':          { brand: 'WELL',      tier: 'pro',        price: 79 },
  'well-enterprise':   { brand: 'WELL',      tier: 'enterprise', price: 199 },
  'algo-trader':       { brand: 'ALGO',      tier: 'starter',    price: 49 },
  'algo-pro':          { brand: 'ALGO',      tier: 'pro',        price: 149 },
  'algo-quant':        { brand: 'ALGO',      tier: 'enterprise', price: 499 },
  'apex-starter':      { brand: 'APEX',      tier: 'starter',    price: 39 },
  'apex-pro':          { brand: 'APEX',      tier: 'pro',        price: 99 },
  'apex-enterprise':   { brand: 'APEX',      tier: 'enterprise', price: 299 },
  'sdk-builder':       { brand: 'AGENCYOS',  tier: 'starter',    price: 19 },
  'sdk-pro':           { brand: 'AGENCYOS',  tier: 'pro',        price: 49 },
  'sdk-agency':        { brand: 'AGENCYOS',  tier: 'enterprise', price: 99 },
};

// ---------------------------------------------------------------------------
// Signature verification
// ---------------------------------------------------------------------------

/**
 * Verify a Polar.sh webhook signature using HMAC-SHA256.
 * Polar sends: `webhook-signature: sha256=<hex>`
 */
export function verifyPolarSignature(
  payload: string,
  signature: string,
  secret: string,
): boolean {
  const expected = createHmac('sha256', secret).update(payload).digest('hex');
  const provided = signature.startsWith('sha256=') ? signature.slice(7) : signature;

  if (expected.length !== provided.length) return false;

  // Constant-time comparison to prevent timing attacks
  let mismatch = 0;
  for (let i = 0; i < expected.length; i++) {
    mismatch |= expected.charCodeAt(i) ^ provided.charCodeAt(i);
  }
  return mismatch === 0;
}

// ---------------------------------------------------------------------------
// Webhook handler
// ---------------------------------------------------------------------------

/**
 * Route a Polar webhook event and return a structured result.
 * Supports: checkout.completed, subscription.cancelled
 */
export function handlePolarWebhook(event: PolarWebhookEvent): WebhookResult {
  const { type, data } = event;

  if (type === 'checkout.completed') {
    const config = POLAR_PRODUCTS[data.product_id];

    if (!config) {
      return {
        success: false,
        action: 'error',
        error: `Unknown product_id: ${data.product_id}`,
      };
    }

    try {
      const licenseKey = generateKey(config.brand, config.tier, data.customer_email);

      return {
        success: true,
        action: 'key_issued',
        key: licenseKey.key,
        brand: config.brand,
        tier: config.tier,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { success: false, action: 'error', error: message };
    }
  }

  if (type === 'subscription.cancelled') {
    const config = POLAR_PRODUCTS[data.product_id];

    return {
      success: true,
      action: 'subscription_cancelled',
      brand: config?.brand,
      tier: config?.tier,
    };
  }

  return { success: true, action: 'ignored' };
}
