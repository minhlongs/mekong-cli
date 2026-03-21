/**
 * Billing resource — pricing tiers, credit packs, Stripe checkout
 */

import type { HttpRequester } from '../http-requester.js';
import type {
  PricingTier, CreditPack,
  CreateCheckoutParams, CreateCheckoutResponse,
} from '../types.js';

export class BillingResource {
  constructor(private readonly http: HttpRequester) {}

  getPricing(): Promise<PricingTier[]> {
    return this.http.get('/billing/pricing');
  }

  getCreditPacks(): Promise<CreditPack[]> {
    return this.http.get('/billing/stripe/packs');
  }

  createCheckout(params: CreateCheckoutParams): Promise<CreateCheckoutResponse> {
    return this.http.post('/billing/stripe/checkout', params);
  }
}
