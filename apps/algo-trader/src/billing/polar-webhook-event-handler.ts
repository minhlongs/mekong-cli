/**
 * Polar.sh Webhook Event Handler — processes subscription lifecycle events.
 * Verifies webhook signature, routes events to subscription service.
 * Events: subscription.created, subscription.active, subscription.updated,
 *         subscription.canceled, subscription.revoked, order.created, refund.created
 */

import { createHmac, timingSafeEqual } from 'crypto';
import { z } from 'zod';
import { PolarSubscriptionService, TenantTier } from './polar-subscription-service';
import { LicenseService, LicenseTier } from '../lib/raas-gate';
import { PolarAuditLogger } from './polar-audit-logger';

const WEBHOOK_SECRET = process.env.POLAR_WEBHOOK_SECRET ?? '';

function mapTenantTierToLicenseTier(tenantTier: TenantTier): LicenseTier {
  switch (tenantTier) {
    case 'pro':
      return LicenseTier.PRO;
    case 'enterprise':
      return LicenseTier.ENTERPRISE;
    default:
      return LicenseTier.FREE;
  }
}

export const PolarWebhookPayloadSchema = z.object({
  type: z.string(),
  data: z.looseObject({
    id: z.string(),
    status: z.string().optional(),
    product_id: z.string().optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
    current_period_end: z.string().nullable().optional(),
    subscription_id: z.string().optional(),
    amount: z.number().optional(),
  }),
});

export type PolarWebhookPayload = z.infer<typeof PolarWebhookPayloadSchema>;

export interface WebhookResult {
  handled: boolean;
  event: string;
  tenantId: string | null;
  tier: TenantTier | null;
  action: 'activated' | 'updated' | 'deactivated' | 'ignored' | 'refunded';
  idempotencyKey?: string;
}

export class PolarWebhookEventHandler {
  private licenseService: LicenseService;
  private subscriptionService: PolarSubscriptionService;
  private auditLogger: PolarAuditLogger;

  constructor(
    subscriptionService?: PolarSubscriptionService,
    private onTierChange?: (tenantId: string, newTier: TenantTier) => void,
  ) {
    this.licenseService = LicenseService.getInstance();
    this.subscriptionService = subscriptionService ?? PolarSubscriptionService.getInstance();
    this.auditLogger = PolarAuditLogger.getInstance();
  }

  /**
   * Verify Polar webhook signature (HMAC-SHA256).
   * Returns true if signature valid or no secret configured (dev mode).
   */
  verifySignature(payload: string, signature: string): boolean {
    if (!WEBHOOK_SECRET) {
      return true;
    }

    const expected = createHmac('sha256', WEBHOOK_SECRET)
      .update(payload)
      .digest('hex');

    const sigHex = signature.replace('sha256=', '');
    if (expected.length !== sigHex.length) return false;
    return timingSafeEqual(Buffer.from(expected), Buffer.from(sigHex));
  }

  /** Process a webhook event payload with idempotency check. */
  handleEvent(payload: PolarWebhookPayload): WebhookResult {
    const eventId = payload.data.id;
    const tenantId = this.extractTenantId(payload);

    // Idempotency check
    if (eventId && this.auditLogger.isProcessed(eventId)) {
      return {
        handled: true,
        event: payload.type,
        tenantId,
        tier: null,
        action: 'ignored',
        idempotencyKey: eventId,
      };
    }

    let result: WebhookResult;

    switch (payload.type) {
      case 'subscription.created':
      case 'subscription.active':
        result = this.handleActivation(payload, tenantId);
        break;

      case 'subscription.updated':
        result = this.handleUpdate(payload, tenantId);
        break;

      case 'subscription.canceled':
      case 'subscription.revoked':
        result = this.handleCancellation(tenantId, payload.type);
        break;

      case 'order.created':
        result = this.handleOrderCreated(payload, tenantId);
        break;

      case 'refund.created':
        result = this.handleRefundCreated(payload, tenantId);
        break;

      default:
        result = {
          handled: false,
          event: payload.type,
          tenantId,
          tier: null,
          action: 'ignored',
        };
    }

    // Mark as processed and log
    if (eventId) {
      this.auditLogger.markProcessed(eventId);
    }
    this.auditLogger.log({
      eventId: eventId || `unknown_${Date.now()}`,
      eventType: payload.type,
      tenantId,
      timestamp: new Date().toISOString(),
      action: result.action,
      success: result.handled,
      idempotencyKey: result.idempotencyKey || eventId || undefined,
    });

    return result;
  }

  private handleActivation(payload: PolarWebhookPayload, tenantId: string | null): WebhookResult {
    if (!tenantId || !payload.data.product_id) {
      return { handled: false, event: payload.type, tenantId, tier: null, action: 'ignored' };
    }

    const tier = this.subscriptionService.getTierByProductId(payload.data.product_id);
    if (!tier) {
      return { handled: false, event: payload.type, tenantId, tier: null, action: 'ignored' };
    }

    this.subscriptionService.activateSubscription(
      tenantId,
      tier,
      payload.data.product_id,
      payload.data.current_period_end ?? null,
    );

    const licenseTier = mapTenantTierToLicenseTier(tier);
    this.licenseService.activateSubscription(tenantId, licenseTier, payload.data.id || payload.data.product_id);
    this.onTierChange?.(tenantId, tier);

    return { handled: true, event: payload.type, tenantId, tier, action: 'activated' };
  }

  private handleUpdate(payload: PolarWebhookPayload, tenantId: string | null): WebhookResult {
    if (!tenantId || !payload.data.product_id) {
      return { handled: false, event: payload.type, tenantId, tier: null, action: 'ignored' };
    }

    const tier = this.subscriptionService.getTierByProductId(payload.data.product_id);
    if (!tier) {
      return { handled: false, event: payload.type, tenantId, tier: null, action: 'ignored' };
    }

    this.subscriptionService.activateSubscription(
      tenantId,
      tier,
      payload.data.product_id,
      payload.data.current_period_end ?? null,
    );

    const licenseTier = mapTenantTierToLicenseTier(tier);
    this.licenseService.activateSubscription(tenantId, licenseTier, payload.data.id || payload.data.product_id);
    this.onTierChange?.(tenantId, tier);

    return { handled: true, event: payload.type, tenantId, tier, action: 'updated' };
  }

  private handleCancellation(tenantId: string | null, event: string): WebhookResult {
    if (!tenantId) {
      return { handled: false, event, tenantId, tier: null, action: 'ignored' };
    }

    this.subscriptionService.deactivateSubscription(tenantId);
    this.licenseService.deactivateSubscription(tenantId);
    this.onTierChange?.(tenantId, 'free');

    return { handled: true, event, tenantId, tier: 'free', action: 'deactivated' };
  }

  private handleOrderCreated(payload: PolarWebhookPayload, tenantId: string | null): WebhookResult {
    if (!tenantId || !payload.data.product_id) {
      return { handled: false, event: 'order.created', tenantId, tier: null, action: 'ignored' };
    }

    const tier = this.subscriptionService.getTierByProductId(payload.data.product_id);
    if (!tier) {
      return { handled: false, event: 'order.created', tenantId, tier: null, action: 'ignored' };
    }

    // One-time purchase = activate for lifetime (no period end)
    this.subscriptionService.activateSubscription(tenantId, tier, payload.data.product_id, null);

    const licenseTier = mapTenantTierToLicenseTier(tier);
    this.licenseService.activateSubscription(tenantId, licenseTier, payload.data.id || payload.data.product_id);
    this.auditLogger.logOrder(tenantId, payload.data.id, payload.data.product_id);
    this.onTierChange?.(tenantId, tier);

    return { handled: true, event: 'order.created', tenantId, tier, action: 'activated' };
  }

  private handleRefundCreated(payload: PolarWebhookPayload, tenantId: string | null): WebhookResult {
    if (!tenantId) {
      return { handled: false, event: 'refund.created', tenantId, tier: null, action: 'ignored' };
    }

    const subscriptionId = payload.data.subscription_id || payload.data.id;

    // Deactivate subscription
    this.subscriptionService.deactivateSubscription(tenantId);
    this.licenseService.deactivateSubscription(tenantId);
    this.onTierChange?.(tenantId, 'free');

    // Log refund alert
    const amount = payload.data.amount || 0;
    this.auditLogger.logRefund(tenantId, subscriptionId || 'unknown', amount);

    return { handled: true, event: 'refund.created', tenantId, tier: 'free', action: 'refunded' };
  }

  private extractTenantId(payload: PolarWebhookPayload): string | null {
    const metadata = payload.data.metadata;
    if (metadata && typeof metadata.tenantId === 'string') {
      return metadata.tenantId;
    }
    return null;
  }
}
