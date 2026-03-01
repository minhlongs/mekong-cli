/**
 * Autonomous webhook handler types
 *
 * Dependency-injected interfaces for webhook processing pipeline.
 * Extracted from @agencyos/vibe-payment/autonomous-webhook-handler.
 */

/** Order record from database (webhook lookup target) */
export interface OrderRecord {
  id: string;
  status: string;
  userId: string | null;
  orderCode: number;
}

/** Subscription intent record (pending payment → activation) */
export interface SubscriptionIntentRecord {
  id: string;
  userId: string;
  planId: string;
  billingCycle: 'monthly' | 'yearly';
  status: string;
  orgId?: string | null;
}

/** Dependency injection for autonomous webhook handler */
export interface WebhookHandlerDeps {
  findOrder: (orderCode: number) => Promise<OrderRecord | null>;
  findSubscriptionIntent: (orderCode: number) => Promise<SubscriptionIntentRecord | null>;
  updateOrderStatus: (orderId: string, fromStatus: string, toStatus: string, paymentData: Record<string, unknown>) => Promise<boolean>;
  updateSubscriptionIntent: (intentId: string, status: string) => Promise<void>;
  activateSubscription: (intent: SubscriptionIntentRecord) => Promise<void>;
  logAudit: (userId: string | null, action: string, payload: Record<string, unknown>, severity: string) => Promise<void>;
}

/** Valid payment status transitions (state machine) */
export type PaymentStatusTransitions = Record<string, string[]>;
