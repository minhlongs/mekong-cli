/**
 * @agencyos/vibe-payos-billing-types — PayOS Billing Orchestrator Types
 *
 * Pure type definitions extracted from @agencyos/vibe-payment for reuse
 * across billing, webhook handling, and analytics modules.
 *
 * Sub-path imports:
 *   import type { PayOSWebhookData } from '@agencyos/vibe-payos-billing-types/webhook-data';
 *   import type { BillingOrchestrationDeps } from '@agencyos/vibe-payos-billing-types/orchestration';
 *   import type { OrderRecord } from '@agencyos/vibe-payos-billing-types/handler';
 *   import type { PaymentEvent } from '@agencyos/vibe-payos-billing-types/analytics';
 */

// ─── PayOS Webhook Data ─────────────────────────────────────────

export type {
  PayOSWebhookData,
  PayOSWebhookPayload,
  PayOSTransactionCode,
} from './payos-webhook-data-types';

export { PAYOS_CODE_MAP } from './payos-webhook-data-types';

// ─── Autonomous Webhook Handler ─────────────────────────────────

export type {
  OrderRecord,
  SubscriptionIntentRecord,
  WebhookHandlerDeps,
  PaymentStatusTransitions,
} from './autonomous-webhook-handler-types';

// ─── Billing Orchestration ──────────────────────────────────────

export type {
  BillingOrchestrationDeps,
  BillingOrchestrationResult,
  BillingWebhookFactoryConfig,
} from './billing-orchestration-types';

// ─── Payment Analytics ──────────────────────────────────────────

export type {
  PaymentProviderName,
  PaymentStatusCode,
  PaymentEvent,
  PaymentMetricsSummary,
  RevenueByPeriod,
  PaymentAnalyticsQuery,
} from './payment-analytics-types';
