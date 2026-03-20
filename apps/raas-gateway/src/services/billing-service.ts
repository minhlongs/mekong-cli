/**
 * Billing Service — Polar.sh webhook integration
 */

import type { Env } from '../index';

export interface PolarOrder {
  id: string;
  customer_id: string;
  product_id: string;
  product_name: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
  metadata?: Record<string, string>;
}

export interface PolarSubscription {
  id: string;
  customer_id: string;
  product_id: string;
  product_name: string;
  status: 'active' | 'canceled' | 'expired';
  current_period_start: string;
  current_period_end: string;
}

export interface PolarCustomer {
  id: string;
  email: string;
  external_id?: string; // tenant_id reference
}

export interface PolarEvent {
  id: string;
  type: string;
  data: {
    order?: PolarOrder;
    subscription?: PolarSubscription;
    customer?: PolarCustomer;
  };
  created_at: string;
  timestamp?: string;
}

export interface CreditAllocation {
  credits: number;
  tier?: 'starter' | 'pro' | 'enterprise';
}

// Product to credit mapping
export const POLAR_PRODUCT_CREDITS: Record<string, CreditAllocation> = {
  // Subscription tiers
  'agencyos-starter': { credits: 50, tier: 'pro' },
  'agencyos-pro': { credits: 200, tier: 'pro' },
  'agencyos-agency': { credits: 500, tier: 'enterprise' },
  'agencyos-master': { credits: 1000, tier: 'enterprise' },
  // Credit packs
  'credits-10': { credits: 10 },
  'credits-50': { credits: 50 },
  'credits-100': { credits: 100 },
  'credits-500': { credits: 500 },
};

export class BillingService {
  constructor(private env: Env) {}

  /**
   * Verify Polar webhook signature
   * Returns true if signature is valid (or no secret configured)
   */
  async verifySignature(payload: string, signature: string): Promise<boolean> {
    const secret = this.env.POLAR_WEBHOOK_SECRET;

    // Skip verification if no secret (dev mode)
    if (!secret) {
      console.warn('[BillingService] No POLAR_WEBHOOK_SECRET configured, skipping verification');
      return true;
    }

    try {
      // HMAC-SHA256 verification
      const keyData = new TextEncoder().encode(secret);
      const msgData = new TextEncoder().encode(payload);

      const cryptoKey = await crypto.subtle.importKey(
        'raw',
        keyData,
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
      );

      const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, msgData);
      const expectedSig = Array.from(new Uint8Array(sigBuffer))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');

      return signature === expectedSig;
    } catch (error) {
      console.error('[BillingService] Signature verification error:', error);
      return false;
    }
  }

  /**
   * Check for duplicate webhook event (idempotency)
   * Returns true if event already processed
   */
  async isDuplicateEvent(eventId: string): Promise<boolean> {
    const result = await this.env.DB.prepare(
      'SELECT id FROM webhook_events WHERE event_id = ?'
    )
      .bind(eventId)
      .first<{ id: string }>();

    return !!result;
  }

  /**
   * Record webhook event to prevent replay attacks
   */
  async recordEvent(eventId: string, eventType: string, processed: boolean = true): Promise<void> {
    await this.env.DB.prepare(
      `INSERT INTO webhook_events (id, event_id, event_type, processed, created_at)
       VALUES (?, ?, ?, ?, ?)`
    )
      .bind(
        crypto.randomUUID(),
        eventId,
        eventType,
        processed ? 1 : 0,
        new Date().toISOString()
      )
      .run();
  }

  /**
   * Validate event timestamp (prevent replay attacks)
   * Returns true if timestamp is within acceptable window (5 minutes)
   */
  isValidTimestamp(timestamp: string): boolean {
    const eventTime = new Date(timestamp).getTime();
    const now = Date.now();
    const age = now - eventTime;

    // Reject if older than 5 minutes
    if (age > 5 * 60 * 1000) {
      return false;
    }

    // Reject if in future
    if (age < 0) {
      return false;
    }

    return true;
  }

  /**
   * Extract tenant_id from event data
   * Supports multiple sources for flexibility
   */
  extractTenantId(event: PolarEvent): string | null {
    const { data } = event;

    // Direct tenant_id in metadata
    if (data.order?.metadata?.tenant_id) {
      return data.order.metadata.tenant_id;
    }

    // Customer external_id (our tenant_id)
    if (data.customer?.external_id) {
      return data.customer.external_id;
    }

    // Order metadata
    if ((data as any).metadata?.tenant_id) {
      return (data as any).metadata.tenant_id;
    }

    return null;
  }

  /**
   * Get credit allocation for product
   */
  getProductCredits(productName: string): CreditAllocation | null {
    const key = productName.toLowerCase().replace(/\s+/g, '-');
    return POLAR_PRODUCT_CREDITS[key] || null;
  }

  /**
   * Process order.paid event
   * Allocates credits and updates tier if subscription
   */
  async processOrderPaid(event: PolarEvent): Promise<{ success: boolean; credits?: number; tier?: string }> {
    const tenantId = this.extractTenantId(event);
    if (!tenantId) {
      console.error('[BillingService] No tenant_id found in order.paid event');
      return { success: false };
    }

    const productName = event.data.order?.product_name || '';
    const allocation = this.getProductCredits(productName);

    if (!allocation || allocation.credits <= 0) {
      console.warn('[BillingService] No credit allocation for product:', productName);
      return { success: false };
    }

    // Import CreditService dynamically to avoid circular dependency
    const { CreditService } = await import('./credit-service');
    const creditService = new CreditService(this.env);

    // Add credits
    const newBalance = await creditService.addCredits(
      tenantId,
      allocation.credits,
      'purchase',
      `Polar.sh: ${productName}`,
      {
        order_id: event.data.order?.id,
        product_name: productName,
        event_id: event.id,
      }
    );

    // Update tier if subscription
    if (allocation.tier) {
      await this.updateTenantTier(tenantId, allocation.tier);
    }

    console.log(`[BillingService] Allocated ${allocation.credits} credits to ${tenantId}, new balance: ${newBalance}`);

    return {
      success: true,
      credits: allocation.credits,
      tier: allocation.tier,
    };
  }

  /**
   * Process subscription.active event
   * Updates tenant tier
   */
  async processSubscriptionActive(event: PolarEvent): Promise<{ success: boolean; tier?: string }> {
    const tenantId = this.extractTenantId(event);
    if (!tenantId) {
      console.error('[BillingService] No tenant_id found in subscription.active event');
      return { success: false };
    }

    const productName = event.data.subscription?.product_name || '';
    const allocation = this.getProductCredits(productName);

    if (allocation?.tier) {
      await this.updateTenantTier(tenantId, allocation.tier);
      console.log(`[BillingService] Upgraded ${tenantId} to ${allocation.tier}`);
      return { success: true, tier: allocation.tier };
    }

    return { success: false };
  }

  /**
   * Process subscription.canceled event
   * Downgrades tenant to starter tier
   */
  async processSubscriptionCanceled(event: PolarEvent): Promise<{ success: boolean }> {
    const tenantId = this.extractTenantId(event);
    if (!tenantId) {
      console.error('[BillingService] No tenant_id found in subscription.canceled event');
      return { success: false };
    }

    await this.updateTenantTier(tenantId, 'starter');
    console.log(`[BillingService] Downgraded ${tenantId} to starter (subscription canceled)`);

    return { success: true };
  }

  /**
   * Process refund.created event
   * Deducts credits from tenant
   */
  async processRefund(event: PolarEvent): Promise<{ success: boolean; deducted?: number }> {
    const tenantId = this.extractTenantId(event);
    if (!tenantId) {
      console.error('[BillingService] No tenant_id found in refund event');
      return { success: false };
    }

    const orderAmount = event.data.order?.amount || 0;
    const productName = event.data.order?.product_name || '';
    const allocation = this.getProductCredits(productName);

    if (!allocation || allocation.credits <= 0) {
      console.warn('[BillingService] No credit allocation for refund:', productName);
      return { success: false };
    }

    const { CreditService } = await import('./credit-service');
    const creditService = new CreditService(this.env);

    const result = await creditService.deduct(
      tenantId,
      allocation.credits,
      'adjustment',
      `Refund: ${productName} (Order: ${event.data.order?.id})`
    );

    if (result.success) {
      console.log(`[BillingService] Deducted ${allocation.credits} credits from ${tenantId} for refund`);
      return { success: true, deducted: allocation.credits };
    }

    console.error('[BillingService] Failed to deduct credits for refund:', result.error);
    return { success: false };
  }

  /**
   * Update tenant tier
   */
  private async updateTenantTier(tenantId: string, tier: string): Promise<void> {
    await this.env.DB.prepare(
      'UPDATE tenants SET tier = ?, updated_at = datetime(\'now\') WHERE id = ?'
    )
      .bind(tier, tenantId)
      .run();
  }
}
