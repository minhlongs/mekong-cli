/**
 * Payment analytics types for billing dashboards
 *
 * Pure type definitions — no runtime dependencies.
 * Extracted from @agencyos/vibe-payment/payment-analytics-types.
 */

/** Supported payment provider names */
export type PaymentProviderName = 'payos' | 'vnpay' | 'momo' | 'stripe';

/** Payment status codes */
export type PaymentStatusCode = 'PENDING' | 'PAID' | 'CANCELLED' | 'FAILED';

/** Individual payment event for audit/analytics */
export interface PaymentEvent {
  id: string;
  orderCode: number;
  provider: PaymentProviderName;
  status: PaymentStatusCode;
  amount: number;
  currency: string;
  userId: string | null;
  orgId: string | null;
  isSubscription: boolean;
  planSlug: string | null;
  billingCycle: 'monthly' | 'yearly' | null;
  createdAt: string;
  completedAt: string | null;
  metadata: Record<string, unknown>;
}

/** Aggregated metrics for a billing period */
export interface PaymentMetricsSummary {
  totalRevenue: number;
  totalTransactions: number;
  successRate: number;
  averageOrderValue: number;
  subscriptionRevenue: number;
  oneTimeRevenue: number;
  refundedAmount: number;
  currency: string;
  periodStart: string;
  periodEnd: string;
}

/** Revenue breakdown by time period */
export interface RevenueByPeriod {
  period: string;
  revenue: number;
  transactionCount: number;
  newSubscriptions: number;
  renewals: number;
  churned: number;
}

/** Query params for fetching payment analytics */
export interface PaymentAnalyticsQuery {
  startDate: string;
  endDate: string;
  provider?: PaymentProviderName;
  orgId?: string;
  groupBy?: 'day' | 'week' | 'month';
  includeRefunds?: boolean;
}
