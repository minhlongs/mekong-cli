/**
 * Billing orchestration pipeline types
 *
 * Types for the Payment→Subscription→Tenant pipeline.
 * Extracted from @agencyos/vibe-payment/billing-webhook-orchestrator.
 */

import type { WebhookHandlerDeps } from './autonomous-webhook-handler-types';

/** Extended deps for billing orchestration (adds tenant resolution + notifications) */
export interface BillingOrchestrationDeps extends WebhookHandlerDeps {
  resolveTenantFromOrg?: (orgId: string) => Promise<{ orgSlug: string; orgName: string } | null>;
  onBillingComplete?: (result: BillingOrchestrationResult) => Promise<void>;
}

/** Full result from billing orchestration pipeline */
export interface BillingOrchestrationResult {
  webhookResult: { status: string; orderCode?: number; newStatus?: string; message?: string };
  event: { orderCode: number; amount: number; type: string } | null;
  tenantContext: { orgSlug: string; orgName: string } | null;
  timestamp: string;
}

/** Config for creating billing webhook handlers */
export interface BillingWebhookFactoryConfig {
  webhookSecret: string;
  checksumKey: string;
  onPaymentSuccess?: (event: unknown, orderId: string) => Promise<void>;
  onPaymentCancelled?: (event: unknown, orderId: string) => Promise<void>;
}
