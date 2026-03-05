/**
 * Polar.sh Webhook Handler
 *
 * Handles subscription lifecycle events for RaaS license gating.
 */

import { createHmac } from 'crypto';
import { LicenseService, LicenseTier } from './raas-gate';

export interface WebhookEvent {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface WebhookHandlerResult {
  success: boolean;
  licenseKey?: string;
  newTier?: LicenseTier;
  message?: string;
}

/**
 * Verify webhook signature using HMAC-SHA256
 */
export function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const hmac = createHmac('sha256', secret);
  const computedSignature = hmac.update(payload).digest('hex');
  return signature === `whsec_${computedSignature}`;
}

/**
 * Parse and validate webhook payload
 */
export function parseWebhookPayload(
  rawBody: string,
  signature: string,
  webhookSecret: string
): WebhookEvent {
  if (!verifyWebhookSignature(rawBody, signature, webhookSecret)) {
    throw new Error('Invalid webhook signature');
  }

  const event = JSON.parse(rawBody) as WebhookEvent;

  // Validate timestamp (reject if older than 5 minutes)
  const eventTime = new Date(event.timestamp).getTime();
  const now = Date.now();
  const fiveMinutes = 5 * 60 * 1000;

  if (now - eventTime > fiveMinutes) {
    throw new Error('Webhook timestamp expired');
  }

  return event;
}

/**
 * Handle subscription lifecycle events
 */
export async function handleWebhookEvent(
  event: WebhookEvent
): Promise<WebhookHandlerResult> {
  const licenseService = LicenseService.getInstance();

  switch (event.type) {
    case 'payment.success': {
      const { license_key, tier } = event.data as {
        license_key: string;
        tier?: string
      };

      await licenseService.activateLicense(license_key, tier as LicenseTier || LicenseTier.PRO);

      return {
        success: true,
        licenseKey: license_key,
        newTier: tier as LicenseTier || LicenseTier.PRO,
        message: 'License activated successfully'
      };
    }

    case 'subscription.created': {
      const { license_key, tier } = event.data as {
        license_key: string;
        tier: string
      };

      await licenseService.setTier(license_key, tier as LicenseTier);

      return {
        success: true,
        licenseKey: license_key,
        newTier: tier as LicenseTier,
        message: 'Subscription created'
      };
    }

    case 'subscription.cancelled': {
      const { license_key } = event.data as { license_key: string };

      await licenseService.downgradeToFree(license_key);

      return {
        success: true,
        licenseKey: license_key,
        newTier: LicenseTier.FREE,
        message: 'Subscription cancelled, downgraded to FREE'
      };
    }

    case 'subscription.refunded': {
      const { license_key } = event.data as { license_key: string };

      await licenseService.revokeLicense(license_key);

      return {
        success: true,
        licenseKey: license_key,
        message: 'License revoked due to refund'
      };
    }

    default:
      return {
        success: false,
        message: `Unhandled event type: ${event.type}`
      };
  }
}

/**
 * Main webhook handler for Express/Fastify
 */
export async function webhookHandler(
  rawBody: string,
  signature: string,
  webhookSecret: string
): Promise<WebhookHandlerResult> {
  try {
    const event = parseWebhookPayload(rawBody, signature, webhookSecret);
    return await handleWebhookEvent(event);
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Webhook processing failed'
    };
  }
}
