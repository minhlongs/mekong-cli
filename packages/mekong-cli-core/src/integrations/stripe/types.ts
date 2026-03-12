/** Stripe-specific types */

export interface StripeConfig {
  secretKey: string;
  webhookSecret?: string;
  apiVersion?: string;
}

export interface StripeInvoiceItem {
  description: string;
  quantity: number;
  unitAmount: number;              // cents
  currency: string;
}

export interface StripeCustomer {
  id: string;
  email: string;
  name?: string;
  metadata?: Record<string, string>;
}
