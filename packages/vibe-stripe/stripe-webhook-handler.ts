/**
 * @agencyos/vibe-stripe — Stripe Webhook Verification & Event Router
 *
 * Server-side webhook handler with HMAC-SHA256 signature verification,
 * idempotency guard, and event-type routing.
 *
 * Usage:
 *   import { createStripeWebhookHandler } from '@agencyos/vibe-stripe/webhooks';
 *   const handler = createStripeWebhookHandler({
 *     webhookSecret: 'whsec_...',
 *     onCheckoutCompleted: async (session) => { ... },
 *   });
 *   const result = await handler.handleRequest(rawBody, sigHeader);
 */

import type {
  StripeWebhookEvent,
  StripeWebhookHandlers,
  StripeWebhookVerifyResult,
} from './types';

// ─── Webhook Handler Config ─────────────────────────────────────

export interface StripeWebhookHandlerConfig extends StripeWebhookHandlers {
  webhookSecret: string;
  /** Optional idempotency check — return true if event already processed */
  isProcessed?: (eventId: string) => Promise<boolean>;
  /** Optional callback to mark event as processed */
  markProcessed?: (eventId: string, eventType: string) => Promise<void>;
}

// ─── Webhook Processing Result ──────────────────────────────────

export type WebhookResult =
  | { status: 'processed'; eventId: string; eventType: string }
  | { status: 'duplicate'; eventId: string }
  | { status: 'ignored'; eventType: string }
  | { status: 'error'; message: string };

// ─── Webhook Handler ────────────────────────────────────────────

export function createStripeWebhookHandler(config: StripeWebhookHandlerConfig) {
  const { webhookSecret, isProcessed, markProcessed, ...handlers } = config;

  return {
    /**
     * Verify signature and process webhook event.
     * Call this from your HTTP endpoint handler.
     *
     * @param rawBody — Raw request body string (NOT parsed JSON)
     * @param signatureHeader — Value of `Stripe-Signature` header
     */
    async handleRequest(rawBody: string, signatureHeader: string): Promise<WebhookResult> {
      // Step 1: Verify signature via real HMAC-SHA256
      const verification = await verifyStripeSignatureAsync(rawBody, signatureHeader, webhookSecret);
      if (!verification.valid || !verification.event) {
        return { status: 'error', message: verification.error ?? 'Invalid signature' };
      }

      const event = verification.event;

      // Step 2: Idempotency check
      if (isProcessed) {
        const alreadyDone = await isProcessed(event.id);
        if (alreadyDone) {
          return { status: 'duplicate', eventId: event.id };
        }
      }

      // Step 3: Route to handler
      try {
        const handled = await routeEvent(event, handlers);
        if (!handled) {
          return { status: 'ignored', eventType: event.type };
        }

        // Step 4: Mark as processed
        if (markProcessed) {
          await markProcessed(event.id, event.type);
        }

        return { status: 'processed', eventId: event.id, eventType: event.type };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        return { status: 'error', message };
      }
    },

    /** Verify signature only (without processing) */
    async verify(rawBody: string, signatureHeader: string): Promise<StripeWebhookVerifyResult> {
      return verifyStripeSignatureAsync(rawBody, signatureHeader, webhookSecret);
    },
  };
}

// ─── Event Router ───────────────────────────────────────────────

async function routeEvent(event: StripeWebhookEvent, handlers: StripeWebhookHandlers): Promise<boolean> {
  const data = event.data.object;

  switch (event.type) {
    case 'checkout.session.completed':
      if (handlers.onCheckoutCompleted) { await handlers.onCheckoutCompleted(data); return true; }
      return false;
    case 'invoice.payment_succeeded':
      if (handlers.onPaymentSucceeded) { await handlers.onPaymentSucceeded(data); return true; }
      return false;
    case 'invoice.payment_failed':
      if (handlers.onPaymentFailed) { await handlers.onPaymentFailed(data); return true; }
      return false;
    case 'customer.subscription.created':
      if (handlers.onSubscriptionCreated) { await handlers.onSubscriptionCreated(data); return true; }
      return false;
    case 'customer.subscription.updated':
      if (handlers.onSubscriptionUpdated) { await handlers.onSubscriptionUpdated(data); return true; }
      return false;
    case 'customer.subscription.deleted':
      if (handlers.onSubscriptionDeleted) { await handlers.onSubscriptionDeleted(data); return true; }
      return false;
    default:
      return false;
  }
}

// ─── Signature Verification (HMAC-SHA256) ───────────────────────

/** Parse Stripe-Signature header into timestamp + v1 signature */
function parseSigHeader(sigHeader: string): { timestamp: string | undefined; signature: string | undefined } {
  const parts = sigHeader.split(',').reduce<Record<string, string>>((acc, part) => {
    const [key, value] = part.split('=', 2);
    if (key && value) acc[key.trim()] = value.trim();
    return acc;
  }, {});
  return { timestamp: parts['t'], signature: parts['v1'] };
}

/**
 * Async HMAC-SHA256 verification using Web Crypto API.
 * Works in Node.js 18+, Cloudflare Workers, Deno, Bun.
 * Uses constant-time comparison to prevent timing attacks.
 */
export async function verifyStripeSignatureAsync(
  rawBody: string,
  sigHeader: string,
  secret: string,
): Promise<StripeWebhookVerifyResult> {
  try {
    const { timestamp, signature: expectedSig } = parseSigHeader(sigHeader);

    if (!timestamp || !expectedSig) {
      return { valid: false, error: 'Missing timestamp or signature' };
    }

    // Timestamp tolerance check (5 min)
    const now = Math.floor(Date.now() / 1000);
    if (Math.abs(now - parseInt(timestamp, 10)) > 300) {
      return { valid: false, error: 'Timestamp outside tolerance' };
    }

    // HMAC-SHA256 via Web Crypto
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign'],
    );

    const signedPayload = `${timestamp}.${rawBody}`;
    const signatureBuffer = await crypto.subtle.sign('HMAC', key, encoder.encode(signedPayload));
    const computedSig = Array.from(new Uint8Array(signatureBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');

    // Constant-time comparison to prevent timing attacks
    if (computedSig.length !== expectedSig.length) {
      return { valid: false, error: 'Signature mismatch' };
    }
    let mismatch = 0;
    for (let i = 0; i < computedSig.length; i++) {
      mismatch |= computedSig.charCodeAt(i) ^ expectedSig.charCodeAt(i);
    }
    if (mismatch !== 0) {
      return { valid: false, error: 'Signature mismatch' };
    }

    const event = JSON.parse(rawBody) as StripeWebhookEvent;

    // Validate event structure
    if (!event.id || !event.type || !event.data) {
      return { valid: false, error: 'Invalid event structure' };
    }

    return { valid: true, event };
  } catch (err) {
    return { valid: false, error: err instanceof Error ? err.message : 'Async verification failed' };
  }
}
